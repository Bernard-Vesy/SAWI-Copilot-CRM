"""FastAPI entry point for the ClairIA public website and CRM."""
import logging
import secrets
import re
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from mysql.connector import Error as MySQLError
from starlette.middleware.sessions import SessionMiddleware

from .auth import router as auth_router
from .config import settings
from .crud import (
    FormValidationError,
    TABLE_FIELDS,
    form_values,
    validated_record_values,
    visible_fields,
)
from .database import (
    DatabaseConfigurationError,
    check_connection,
    fetch_all,
    fetch_one,
    fetch_record,
    insert_website_request,
    save_record,
)
from .reporting import overview_queries
from .security import csrf_token, current_user, require_csrf, roles_allowed

logger = logging.getLogger(__name__)
BASE = Path(__file__).resolve().parent
app = FastAPI(title="ClairIA CRM", version="1.0.0")
SESSION_SECRET = (
    settings.session_secret
    if settings.session_secret and not settings.session_secret.startswith("<")
    else ""
)
if settings.app_env == "production" and not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET doit être configuré en production.")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET or secrets.token_urlsafe(48),
    https_only=settings.app_env == "production",
    same_site="lax",
    session_cookie="clairia_session",
)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))
app.include_router(auth_router)

NAV = [
    ("Accueil", "/"), ("Services", "/services"), ("À propos", "/a-propos"),
    ("Contact", "/contact"),
]
TABLES = {
    "demandes": ("Demandes Web", "website_requests", "created_at"),
    "prospects": ("Prospects", "prospects", "created_at"),
    "contacts": ("Contacts", "contacts", "created_at"),
    "clients": ("Clients", "clients", "created_at"),
    "opportunites": ("Opportunités", "opportunities", "created_at"),
    "activites": ("Activités", "activities", "created_at"),
    "services": ("Services", "services", "created_at"),
    "devis": ("Devis", "quotes", "created_at"),
    "lignes-devis": ("Lignes de devis", "quote_items", "id"),
    "factures": ("Factures", "invoices", "created_at"),
    "lignes-factures": ("Lignes de facture", "invoice_items", "id"),
    "depenses": ("Dépenses", "expenses", "created_at"),
}
DISPLAY_COLUMNS = {
    "website_requests": ("id", "company_name", "first_name", "last_name", "email",
                         "request_type", "status", "created_at"),
    "prospects": ("id", "company_name", "contact_name", "email", "canton",
                  "source", "status", "potential_value"),
    "contacts": ("id", "first_name", "last_name", "email", "phone", "prospect_id",
                 "client_id"),
    "clients": ("id", "company_name", "industry", "city", "canton", "status"),
    "opportunities": ("id", "title", "estimated_value", "probability", "stage",
                      "expected_close_date"),
    "activities": ("id", "activity_type", "subject", "status", "due_date", "user_id"),
    "services": ("id", "code", "name", "category", "unit_price", "currency", "is_active"),
    "quotes": ("id", "quote_number", "issue_date", "status", "total_amount", "currency"),
    "quote_items": ("id", "quote_id", "service_id", "description", "quantity",
                    "unit_price", "tax_rate", "line_total", "sort_order"),
    "invoices": ("id", "invoice_number", "issue_date", "due_date", "status",
                 "total_amount", "amount_paid", "currency"),
    "invoice_items": ("id", "invoice_id", "service_id", "description", "quantity",
                      "unit_price", "tax_rate", "line_total", "sort_order"),
    "expenses": ("id", "expense_date", "category", "supplier", "total_amount",
                 "payment_status", "currency"),
}


def render(request, page, status_code=200, **context):
    user = context.get("user")
    sections = [(slug, item[0]) for slug, item in TABLES.items()]
    if user and user["role"] == "commercial":
        sections = [(slug, label) for slug, label in sections
                    if TABLES[slug][1] != "website_requests"]
    return templates.TemplateResponse(
        request=request, name=page,
        status_code=status_code,
        context={
            "nav": NAV,
            "sections": sections,
            "csrf_token": csrf_token(request),
            **context,
        },
    )


WRITE_ROLES = {
    "website_requests": ("admin", "manager"),
    "prospects": ("admin", "manager", "commercial"),
    "clients": ("admin", "manager", "commercial"),
    "contacts": ("admin", "manager", "commercial"),
    "opportunities": ("admin", "manager", "commercial"),
    "activities": ("admin", "manager", "commercial"),
    "services": ("admin", "manager"),
    "quotes": ("admin", "manager", "commercial"),
    "quote_items": ("admin", "manager", "commercial"),
    "invoices": ("admin", "manager"),
    "invoice_items": ("admin", "manager"),
    "expenses": ("admin", "manager"),
}


def table_scope(table, user):
    if user["role"] != "commercial":
        return "", ()
    scopes = {
        "prospects": ("`assigned_user_id` = %s", (user["id"],)),
        "clients": ("`assigned_user_id` = %s", (user["id"],)),
        "opportunities": ("`assigned_user_id` = %s", (user["id"],)),
        "activities": ("`user_id` = %s", (user["id"],)),
        "contacts": (
            "(prospect_id IN (SELECT id FROM prospects WHERE assigned_user_id = %s) "
            "OR client_id IN (SELECT id FROM clients WHERE assigned_user_id = %s))",
            (user["id"], user["id"]),
        ),
        "quotes": (
            "(prospect_id IN (SELECT id FROM prospects WHERE assigned_user_id = %s) "
            "OR client_id IN (SELECT id FROM clients WHERE assigned_user_id = %s))",
            (user["id"], user["id"]),
        ),
        "quote_items": (
            "quote_id IN (SELECT id FROM quotes WHERE "
            "(prospect_id IN (SELECT id FROM prospects WHERE assigned_user_id = %s) "
            "OR client_id IN (SELECT id FROM clients WHERE assigned_user_id = %s)))",
            (user["id"], user["id"]),
        ),
        "invoices": (
            "client_id IN (SELECT id FROM clients WHERE assigned_user_id = %s)",
            (user["id"],),
        ),
        "invoice_items": (
            "invoice_id IN (SELECT id FROM invoices WHERE client_id IN "
            "(SELECT id FROM clients WHERE assigned_user_id = %s))",
            (user["id"],),
        ),
        "expenses": ("`created_by` = %s", (user["id"],)),
    }
    return scopes.get(table, ("", ()))


def assert_write_access(table, user):
    allowed = WRITE_ROLES.get(table, ())
    if user["role"] not in allowed:
        raise HTTPException(status_code=403, detail="Modification non autorisée.")


def enforce_commercial_owner(table, user, values):
    if user["role"] != "commercial":
        return values
    owner_column = {
        "prospects": "assigned_user_id",
        "clients": "assigned_user_id",
        "opportunities": "assigned_user_id",
        "activities": "user_id",
        "expenses": "created_by",
    }.get(table)
    if owner_column:
        values[owner_column] = user["id"]
    return values


def validate_related_access(table, values, user):
    if user["role"] != "commercial":
        return
    related_fields = {
        "contacts": ("prospect_id", "prospects", "client_id", "clients"),
        "opportunities": ("prospect_id", "prospects", "client_id", "clients"),
        "activities": (
            "prospect_id", "prospects", "client_id", "clients",
            "opportunity_id", "opportunities", "contact_id", "contacts",
        ),
        "quotes": (
            "prospect_id", "prospects", "client_id", "clients",
            "opportunity_id", "opportunities",
        ),
        "quote_items": ("quote_id", "quotes"),
        "invoices": ("client_id", "clients"),
        "invoice_items": ("invoice_id", "invoices"),
    }.get(table, ())
    for index in range(0, len(related_fields), 2):
        column, related_table = related_fields[index:index + 2]
        related_id = values.get(column)
        if related_id is None:
            continue
        scope_sql, scope_params = table_scope(related_table, user)
        if fetch_record(related_table, related_id, scope_sql, scope_params) is None:
            raise FormValidationError(
                f"Vous ne pouvez pas associer cet enregistrement à « {column} »."
            )


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    problems = settings.database_problems()
    db_state = "not_configured" if not settings.database_enabled else (
        "configuration_incomplete" if problems else "configured"
    )
    if settings.database_enabled and not problems:
        try:
            check_connection()
            db_state = "ready"
        except DatabaseConfigurationError:
            db_state = "configuration_incomplete"
        except MySQLError:
            logger.exception("Readiness database check failed")
            db_state = "unavailable"
    production_config_missing = settings.app_env == "production" and (
        not SESSION_SECRET or not settings.entra_tenant_id or not settings.entra_client_id
        or not settings.entra_client_secret or not settings.database_enabled or bool(problems)
    )
    status = 503 if (
        (settings.database_enabled and (problems or db_state != "ready"))
        or production_config_missing
    ) else 200
    return JSONResponse(
        status_code=status,
        content={
            "status": "ok" if status == 200 else "not_ready",
            "database": db_state,
            "session_signing_key": (
                "configured" if SESSION_SECRET else
                ("ephemeral" if settings.app_env != "production" else "missing")
            ),
        },
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(request, "home.html", title="Accueil")


@app.get("/services", response_class=HTMLResponse)
def services(request: Request):
    return render(request, "services.html", title="Nos services")


@app.get("/a-propos", response_class=HTMLResponse)
def about(request: Request):
    return render(request, "about.html", title="À propos de ClairIA")


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request, sent: bool = False, request_type: str = "contact"):
    if request_type not in ("contact", "diagnostic", "appointment"):
        request_type = "contact"
    return render(request, "contact.html", title="Parlons de votre projet",
                  sent=sent, request_type=request_type)


@app.post("/contact", response_class=HTMLResponse)
async def submit_contact(
    request: Request,
    csrf_token: str = Form(...),
    first_name: str = Form(..., min_length=1, max_length=100),
    last_name: str = Form(..., min_length=1, max_length=100),
    email: str = Form(..., min_length=3, max_length=254),
    request_type: str = Form("contact"),
    company_name: str = Form("", max_length=200),
    phone: str = Form("", max_length=50),
    message: str = Form("", max_length=5000),
    preferred_date: str = Form(""),
):
    require_csrf(request, csrf_token)
    if request_type not in ("contact", "diagnostic", "appointment"):
        raise HTTPException(status_code=422, detail="Type de demande invalide.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=422, detail="Adresse e-mail invalide.")
    if preferred_date:
        from datetime import date
        try:
            date.fromisoformat(preferred_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Date souhaitée invalide.")
    try:
        insert_website_request({
            "company_name": company_name.strip(),
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": email.strip().lower(),
            "phone": phone.strip(),
            "request_type": request_type,
            "message": message.strip(),
            "preferred_date": preferred_date.strip() or None,
        })
    except DatabaseConfigurationError:
        return render(
            request, "contact.html", title="Parlons de votre projet",
            sent=False, error="Formulaire indisponible : la base de test n’est pas configurée. "
                              "Votre demande n’a pas été enregistrée.",
            request_type=request_type, status_code=503,
        )
    except MySQLError:
        logger.exception("Public contact request insert failed")
        # Do not expose SQL, credentials, or connector internals to the public.
        return render(
            request, "contact.html", title="Parlons de votre projet",
            sent=False, error="Un problème empêche l’enregistrement. Réessayez plus tard.",
            request_type=request_type, status_code=503,
        )
    return RedirectResponse("/contact?sent=true", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login(request: Request):
    return render(request, "login.html", title="Connexion au CRM",
                  local_login=settings.app_env != "production",
                  entra_enabled=bool(settings.entra_tenant_id and settings.entra_client_id
                                     and settings.entra_client_secret))


@app.get("/crm", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(current_user)):
    try:
        queries = overview_queries(user)
        list_keys = {
            "opportunities", "prospects", "by_canton", "by_source",
            "by_service", "monthly_revenue", "pipeline_by_owner",
        }
        data = {
            key: fetch_all(sql, params) if key in list_keys else fetch_one(sql, params)
            for key, (sql, params) in queries.items()
        }
    except DatabaseConfigurationError:
        return render(request, "crm.html", title="Tableau de bord", user=user,
                      database_error="Base non configurée. Consultez .env.example; aucun accès distant n’a été tenté.")
    except MySQLError:
        logger.exception("CRM dashboard query failed")
        return render(request, "crm.html", title="Tableau de bord", user=user,
                      database_error="Base inaccessible. Vérifiez la configuration réseau et TLS.")
    return render(request, "crm.html", title="Tableau de bord", user=user,
                  data=data, database_error=None)


@app.get("/crm/{section}", response_class=HTMLResponse)
def crm_section(request: Request, section: str, user=Depends(current_user)):
    if section not in TABLES:
        raise HTTPException(status_code=404, detail="Section CRM inconnue.")
    label, table, _ = TABLES[section]
    if table == "website_requests" and user["role"] == "commercial":
        raise HTTPException(status_code=403, detail="Accès réservé à admin et manager.")
    columns = DISPLAY_COLUMNS[table]
    # Identifiers come from the server-side allowlist; values are bound.
    scope, params = table_scope(table, user)
    where = " WHERE " + scope if scope else ""
    try:
        rows = fetch_all(
            "SELECT " + ", ".join("`" + c + "`" for c in columns) +
            " FROM `" + table + "`" + where + " ORDER BY `id` DESC LIMIT 100",
            params,
        )
    except DatabaseConfigurationError:
        rows = None
        error = "Base non configurée. Aucun accès distant n’a été tenté."
    except MySQLError:
        logger.exception("CRM list query failed for table %s", table)
        rows = None
        error = "Base inaccessible. Vérifiez la configuration réseau et TLS."
    else:
        error = None
    return render(request, "table.html", title=label, label=label, columns=columns,
                  rows=rows, error=error, user=user, section=section,
                  can_write=user["role"] in WRITE_ROLES.get(table, ()),
                  saved=request.query_params.get("saved") == "1")


def _section_table(section):
    if section not in TABLES:
        raise HTTPException(status_code=404, detail="Section CRM inconnue.")
    table = TABLES[section][1]
    if table not in TABLE_FIELDS:
        raise HTTPException(status_code=404, detail="Cette section n’est pas modifiable.")
    return table


def _form_submission_values(table, form):
    values = {}
    for field in TABLE_FIELDS[table]:
        value = form.get(field.name)
        if field.kind == "checkbox" and value is None:
            values[field.name] = "false"
        elif value is not None:
            values[field.name] = str(value)
    return values


def _render_record_form(request, section, table, user, mode, values, error=None,
                        status_code=200, record_id=None):
    label = TABLES[section][0]
    title = ("Créer " if mode == "create" else "Modifier ") + label.lower()
    return render(
        request, "record_form.html", status_code=status_code, title=title,
        label=label, section=section, mode=mode, record_id=record_id,
        fields=visible_fields(table, user), values=values, form_error=error,
        user=user,
    )


@app.get("/crm/{section}/new", response_class=HTMLResponse)
def new_record(request: Request, section: str, user=Depends(current_user)):
    table = _section_table(section)
    assert_write_access(table, user)
    return _render_record_form(
        request, section, table, user, "create", form_values(table)
    )


@app.post("/crm/{section}/new", response_class=HTMLResponse)
async def create_record(request: Request, section: str, user=Depends(current_user)):
    table = _section_table(section)
    assert_write_access(table, user)
    form = await request.form()
    require_csrf(request, str(form.get("csrf_token", "")))
    raw_values = _form_submission_values(table, form)
    try:
        values = enforce_commercial_owner(
            table, user, validated_record_values(table, form, user)
        )
        validate_related_access(table, values, user)
        save_record(table, None, values)
    except FormValidationError as exc:
        return _render_record_form(
            request, section, table, user, "create", form_values(table, raw_values),
            error=str(exc), status_code=422,
        )
    except DatabaseConfigurationError:
        return _render_record_form(
            request, section, table, user, "create", form_values(table, raw_values),
            error="Base de test non configurée; aucune donnée n’a été enregistrée.",
            status_code=503,
        )
    except MySQLError as exc:
        logger.exception("CRM create failed for table %s", table)
        return _render_record_form(
            request, section, table, user, "create", form_values(table, raw_values),
            error="Enregistrement impossible. Vérifiez les champs et leurs relations.",
            status_code=422 if exc.errno in (1062, 1452, 3819) else 503,
        )
    return RedirectResponse(f"/crm/{section}?saved=1", status_code=303)


@app.get("/crm/{section}/{record_id}/edit", response_class=HTMLResponse)
def edit_record(request: Request, section: str, record_id: int,
                user=Depends(current_user)):
    table = _section_table(section)
    assert_write_access(table, user)
    scope, params = table_scope(table, user)
    try:
        row = fetch_record(table, record_id, " AND " + scope if scope else "", params)
    except DatabaseConfigurationError:
        return _render_record_form(
            request, section, table, user, "edit", form_values(table),
            error="Base de test non configurée; aucun accès distant n’a été tenté.",
            status_code=503, record_id=record_id,
        )
    except MySQLError:
        logger.exception("CRM record read failed for table %s, id %s", table, record_id)
        return _render_record_form(
            request, section, table, user, "edit", form_values(table),
            error="Base de données indisponible.", status_code=503,
            record_id=record_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail="Enregistrement introuvable.")
    return _render_record_form(
        request, section, table, user, "edit", form_values(table, row),
        record_id=record_id,
    )


@app.post("/crm/{section}/{record_id}/edit", response_class=HTMLResponse)
async def update_record(request: Request, section: str, record_id: int,
                        user=Depends(current_user)):
    table = _section_table(section)
    assert_write_access(table, user)
    form = await request.form()
    require_csrf(request, str(form.get("csrf_token", "")))
    raw_values = _form_submission_values(table, form)
    scope, params = table_scope(table, user)
    scope_sql = " AND " + scope if scope else ""
    try:
        existing = fetch_record(table, record_id, scope_sql, params)
        if existing is None:
            raise HTTPException(status_code=404, detail="Enregistrement introuvable.")
        values = enforce_commercial_owner(
            table, user, validated_record_values(table, form, user)
        )
        validate_related_access(table, values, user)
        saved = save_record(table, record_id, values, scope_sql, params)
        if saved is None:
            raise HTTPException(status_code=404, detail="Enregistrement introuvable.")
    except FormValidationError as exc:
        return _render_record_form(
            request, section, table, user, "edit", form_values(table, raw_values),
            error=str(exc), status_code=422, record_id=record_id,
        )
    except DatabaseConfigurationError:
        return _render_record_form(
            request, section, table, user, "edit", form_values(table, raw_values),
            error="Base de test non configurée; aucune donnée n’a été enregistrée.",
            status_code=503, record_id=record_id,
        )
    except MySQLError as exc:
        logger.exception("CRM update failed for table %s, id %s", table, record_id)
        return _render_record_form(
            request, section, table, user, "edit", form_values(table, raw_values),
            error="Enregistrement impossible. Vérifiez les champs et leurs relations.",
            status_code=422 if exc.errno in (1062, 1452, 3819) else 503,
            record_id=record_id,
        )
    return RedirectResponse(f"/crm/{section}?saved=1", status_code=303)


@app.get("/crm/admin/utilisateurs", response_class=HTMLResponse)
def users(request: Request, user=Depends(roles_allowed("admin"))):
    try:
        rows = fetch_all(
            "SELECT id, first_name, last_name, email, role, is_active, created_at "
            "FROM users ORDER BY id LIMIT 100"
        )
        error = None
    except DatabaseConfigurationError:
        rows, error = None, "Base non configurée."
    except MySQLError:
        logger.exception("CRM user list query failed")
        rows, error = None, "Utilisateurs indisponibles : vérifiez la configuration de la base."
    return render(request, "table.html", title="Utilisateurs", label="Utilisateurs",
                  columns=("id", "first_name", "last_name", "email", "role", "is_active",
                           "created_at"), rows=rows, error=error, user=user)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port)
