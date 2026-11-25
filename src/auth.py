"""Local test login and Microsoft Entra OpenID Connect login."""
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import bcrypt
from mysql.connector import Error as MySQLError

from .config import settings
from .database import DatabaseConfigurationError, fetch_one
from .security import require_csrf

logger = logging.getLogger(__name__)
router = APIRouter()
oauth = OAuth()
if settings.entra_tenant_id and settings.entra_client_id and settings.entra_client_secret:
    oauth.register(
        name="entra",
        client_id=settings.entra_client_id,
        client_secret=settings.entra_client_secret,
        server_metadata_url=(
            "https://login.microsoftonline.com/"
            + settings.entra_tenant_id
            + "/v2.0/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid profile email"},
    )


def _active_user(email):
    return fetch_one(
        "SELECT id, first_name, last_name, email, role, is_active "
        "FROM users WHERE email = %s AND is_active = 1 LIMIT 1",
        (email,),
    )


def _save_user(request, user):
    if not user or user["role"] not in ("admin", "commercial", "manager"):
        raise HTTPException(status_code=403, detail="Compte CRM actif introuvable.")
    request.session.clear()
    request.session["crm_user"] = {"id": user["id"]}


@router.get("/auth/entra")
async def entra_login(request: Request):
    if not (settings.entra_tenant_id and settings.entra_client_id and settings.entra_client_secret):
        raise HTTPException(status_code=503, detail="Connexion Entra non configurée.")
    return await oauth.entra.authorize_redirect(request, settings.entra_redirect_uri)


@router.get("/auth/callback")
async def entra_callback(request: Request):
    token = await oauth.entra.authorize_access_token(request)
    claims = token.get("userinfo") or await oauth.entra.userinfo(token=token)
    email = claims.get("email") or claims.get("preferred_username")
    if not email:
        raise HTTPException(status_code=403, detail="Identité Entra sans adresse e-mail.")
    try:
        user = _active_user(email.strip().lower())
    except DatabaseConfigurationError:
        raise HTTPException(status_code=503, detail="La base CRM n’est pas configurée.")
    except MySQLError:
        logger.exception("Entra account lookup failed")
        raise HTTPException(status_code=503, detail="La base CRM est inaccessible.")
    _save_user(request, user)
    return RedirectResponse("/crm", status_code=303)


@router.post("/auth/local")
async def local_login(request: Request):
    if settings.app_env == "production":
        raise HTTPException(status_code=404, detail="Non disponible.")
    form = await request.form()
    require_csrf(request, str(form.get("csrf_token", "")))
    email = str(form.get("email", "")).strip().lower()
    password = str(form.get("password", ""))
    try:
        account = fetch_one(
            "SELECT id, first_name, last_name, email, role, is_active, password_hash "
            "FROM users WHERE email = %s AND is_active = 1 LIMIT 1", (email,),
        )
    except DatabaseConfigurationError:
        raise HTTPException(
            status_code=503,
            detail="Connexion locale indisponible : la base de test n’est pas configurée.",
        )
    except MySQLError:
        logger.exception("Local login lookup failed")
        raise HTTPException(
            status_code=503,
            detail="Connexion locale indisponible : vérifiez la base de test et sa configuration TLS.",
        )
    if not account or not account.get("password_hash"):
        raise HTTPException(status_code=401, detail="Identifiants invalides.")
    stored = account["password_hash"]
    if isinstance(stored, str):
        stored = stored.encode("utf-8")
    try:
        valid_password = bcrypt.checkpw(password.encode("utf-8"), stored)
    except ValueError:
        valid_password = False
    if not valid_password:
        raise HTTPException(status_code=401, detail="Identifiants invalides.")
    _save_user(request, account)
    return RedirectResponse("/crm", status_code=303)


@router.post("/auth/logout")
async def logout(request: Request):
    form = await request.form()
    require_csrf(request, str(form.get("csrf_token", "")))
    request.session.clear()
    return RedirectResponse("/", status_code=303)
