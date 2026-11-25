"""Allowlisted CRM form fields and validation for the existing MySQL tables."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    kind: str = "text"
    required: bool = False
    choices: tuple = ()
    default: object = None
    max_length: int | None = None
    minimum: Decimal | None = None
    maximum: Decimal | None = None


def _f(name, label, kind="text", required=False, choices=(), default=None,
       max_length=None, minimum=None, maximum=None):
    return Field(name, label, kind, required, choices, default, max_length,
                 minimum, maximum)


ENUMS = {
    "website_requests": {
        "request_type": ("contact", "diagnostic", "appointment"),
        "status": ("new", "processed", "closed"),
    },
    "prospects": {"status": ("new", "contacted", "qualified", "converted", "lost")},
    "clients": {"status": ("active", "inactive", "lost")},
    "services": {"pricing_model": ("fixed", "hourly", "daily", "subscription")},
    "opportunities": {
        "stage": ("qualification", "discovery", "proposal", "negotiation", "won", "lost"),
    },
    "activities": {
        "activity_type": ("call", "email", "meeting", "task", "demo", "other"),
        "status": ("planned", "completed", "cancelled"),
    },
    "quotes": {"status": ("draft", "sent", "accepted", "rejected", "expired")},
    "invoices": {
        "status": ("draft", "sent", "partially_paid", "paid", "overdue", "cancelled"),
    },
    "expenses": {"payment_status": ("pending", "paid")},
}

TABLE_FIELDS = {
    "website_requests": (
        _f("company_name", "Entreprise", max_length=255),
        _f("first_name", "Prénom", required=True, max_length=100),
        _f("last_name", "Nom", required=True, max_length=100),
        _f("email", "E-mail", "email", required=True, max_length=255),
        _f("phone", "Téléphone", max_length=30),
        _f("request_type", "Type de demande", "select", True,
           ENUMS["website_requests"]["request_type"], "contact"),
        _f("message", "Message", "textarea"),
        _f("preferred_date", "Date souhaitée", "datetime"),
        _f("status", "Statut", "select", True,
           ENUMS["website_requests"]["status"], "new"),
        _f("prospect_id", "Prospect associé", "foreign"),
    ),
    "prospects": (
        _f("company_name", "Entreprise", required=True, max_length=255),
        _f("contact_name", "Nom du contact", max_length=200),
        _f("email", "E-mail", "email", max_length=255),
        _f("phone", "Téléphone", max_length=30),
        _f("website", "Site Web", max_length=255),
        _f("industry", "Secteur", max_length=100),
        _f("company_size", "Taille de l’entreprise", "integer", minimum=Decimal("0")),
        _f("address", "Adresse", max_length=255),
        _f("postal_code", "NPA", max_length=20),
        _f("city", "Ville", max_length=100),
        _f("canton", "Canton", max_length=50),
        _f("country", "Pays", default="Suisse", max_length=100),
        _f("source", "Origine", max_length=100),
        _f("status", "Statut", "select", True, ENUMS["prospects"]["status"], "new"),
        _f("potential_value", "Valeur potentielle", "decimal", default="0",
           minimum=Decimal("0")),
        _f("conversion_probability", "Probabilité (%)", "decimal", default="0",
           minimum=Decimal("0"), maximum=Decimal("100")),
        _f("assigned_user_id", "Commercial responsable", "foreign"),
        _f("notes", "Notes", "textarea"),
    ),
    "clients": (
        _f("prospect_id", "Prospect d’origine", "foreign"),
        _f("company_name", "Entreprise", required=True, max_length=255),
        _f("industry", "Secteur", max_length=100),
        _f("company_size", "Taille de l’entreprise", "integer", minimum=Decimal("0")),
        _f("email", "E-mail", "email", max_length=255),
        _f("phone", "Téléphone", max_length=30),
        _f("address", "Adresse", max_length=255),
        _f("postal_code", "NPA", max_length=20),
        _f("city", "Ville", max_length=100),
        _f("canton", "Canton", max_length=50),
        _f("country", "Pays", default="Suisse", max_length=100),
        _f("vat_number", "N° TVA", max_length=50),
        _f("status", "Statut", "select", True, ENUMS["clients"]["status"], "active"),
        _f("assigned_user_id", "Commercial responsable", "foreign"),
        _f("customer_since", "Client depuis", "date"),
        _f("notes", "Notes", "textarea"),
    ),
    "contacts": (
        _f("prospect_id", "Prospect associé", "foreign"),
        _f("client_id", "Client associé", "foreign"),
        _f("first_name", "Prénom", required=True, max_length=100),
        _f("last_name", "Nom", required=True, max_length=100),
        _f("job_title", "Fonction", max_length=150),
        _f("email", "E-mail", "email", max_length=255),
        _f("phone", "Téléphone", max_length=30),
        _f("mobile", "Mobile", max_length=30),
        _f("is_primary", "Contact principal", "checkbox", default=False),
        _f("notes", "Notes", "textarea"),
    ),
    "services": (
        _f("code", "Code", required=True, max_length=50),
        _f("name", "Nom", required=True, max_length=255),
        _f("description", "Description", "textarea"),
        _f("category", "Catégorie", max_length=100),
        _f("pricing_model", "Mode de tarification", "select", True,
           ENUMS["services"]["pricing_model"], "fixed"),
        _f("unit_price", "Prix unitaire", "decimal", True, default="0",
           minimum=Decimal("0")),
        _f("currency", "Devise", default="CHF", max_length=3),
        _f("estimated_duration", "Durée estimée", max_length=100),
        _f("is_active", "Actif", "checkbox", default=True),
    ),
    "opportunities": (
        _f("prospect_id", "Prospect associé", "foreign"),
        _f("client_id", "Client associé", "foreign"),
        _f("title", "Nom de l’opportunité", required=True, max_length=255),
        _f("description", "Description", "textarea"),
        _f("service_id", "Service", "foreign"),
        _f("estimated_value", "Valeur estimée", "decimal", True, default="0",
           minimum=Decimal("0")),
        _f("probability", "Probabilité (%)", "decimal", True, default="0",
           minimum=Decimal("0"), maximum=Decimal("100")),
        _f("stage", "Étape", "select", True, ENUMS["opportunities"]["stage"],
           "qualification"),
        _f("expected_close_date", "Date de clôture prévue", "date"),
        _f("actual_close_date", "Date de clôture réelle", "date"),
        _f("assigned_user_id", "Commercial responsable", "foreign"),
        _f("loss_reason", "Motif de perte", "textarea"),
    ),
    "activities": (
        _f("prospect_id", "Prospect associé", "foreign"),
        _f("client_id", "Client associé", "foreign"),
        _f("opportunity_id", "Opportunité associée", "foreign"),
        _f("contact_id", "Contact associé", "foreign"),
        _f("user_id", "Utilisateur responsable", "foreign", True),
        _f("activity_type", "Type d’activité", "select", True,
           ENUMS["activities"]["activity_type"], "task"),
        _f("subject", "Objet", required=True, max_length=255),
        _f("description", "Description", "textarea"),
        _f("status", "Statut", "select", True,
           ENUMS["activities"]["status"], "planned"),
        _f("due_date", "Échéance", "datetime"),
        _f("completed_at", "Terminée le", "datetime"),
    ),
    "quotes": (
        _f("quote_number", "N° de devis", required=True, max_length=50),
        _f("prospect_id", "Prospect associé", "foreign"),
        _f("client_id", "Client associé", "foreign"),
        _f("opportunity_id", "Opportunité associée", "foreign"),
        _f("issue_date", "Date d’émission", "date", True),
        _f("valid_until", "Valable jusqu’au", "date"),
        _f("status", "Statut", "select", True, ENUMS["quotes"]["status"], "draft"),
        _f("tax_rate", "Taux de TVA (%)", "decimal", default="0",
           minimum=Decimal("0"), maximum=Decimal("100")),
        _f("currency", "Devise", default="CHF", max_length=3),
        _f("notes", "Notes", "textarea"),
    ),
    "quote_items": (
        _f("quote_id", "Devis", "foreign", True),
        _f("service_id", "Service", "foreign"),
        _f("description", "Description", required=True, max_length=255),
        _f("quantity", "Quantité", "decimal", True, default="1",
           minimum=Decimal("0.01")),
        _f("unit_price", "Prix unitaire", "decimal", True, default="0",
           minimum=Decimal("0")),
        _f("tax_rate", "Taux de TVA (%)", "decimal", default="0",
           minimum=Decimal("0"), maximum=Decimal("100")),
        _f("sort_order", "Ordre", "integer", default="0"),
    ),
    "invoices": (
        _f("invoice_number", "N° de facture", required=True, max_length=50),
        _f("client_id", "Client", "foreign", True),
        _f("quote_id", "Devis associé", "foreign"),
        _f("issue_date", "Date d’émission", "date", True),
        _f("due_date", "Date d’échéance", "date", True),
        _f("payment_date", "Date de paiement", "date"),
        _f("status", "Statut", "select", True, ENUMS["invoices"]["status"], "draft"),
        _f("amount_paid", "Montant payé", "decimal", default="0", minimum=Decimal("0")),
        _f("currency", "Devise", default="CHF", max_length=3),
        _f("notes", "Notes", "textarea"),
    ),
    "invoice_items": (
        _f("invoice_id", "Facture", "foreign", True),
        _f("service_id", "Service", "foreign"),
        _f("description", "Description", required=True, max_length=255),
        _f("quantity", "Quantité", "decimal", True, default="1",
           minimum=Decimal("0.01")),
        _f("unit_price", "Prix unitaire", "decimal", True, default="0",
           minimum=Decimal("0")),
        _f("tax_rate", "Taux de TVA (%)", "decimal", default="0",
           minimum=Decimal("0"), maximum=Decimal("100")),
        _f("sort_order", "Ordre", "integer", default="0"),
    ),
    "expenses": (
        _f("expense_date", "Date de dépense", "date", True),
        _f("category", "Catégorie", required=True, max_length=100),
        _f("supplier", "Fournisseur", max_length=255),
        _f("description", "Description", "textarea"),
        _f("amount", "Montant HT", "decimal", True, default="0",
           minimum=Decimal("0")),
        _f("tax_amount", "Montant TVA", "decimal", True, default="0",
           minimum=Decimal("0")),
        _f("currency", "Devise", default="CHF", max_length=3),
        _f("payment_status", "Statut du paiement", "select", True,
           ENUMS["expenses"]["payment_status"], "pending"),
        _f("payment_date", "Date du paiement", "date"),
        _f("created_by", "Créé par", "foreign"),
    ),
}

OWNER_FIELDS = {
    "prospects": "assigned_user_id",
    "clients": "assigned_user_id",
    "opportunities": "assigned_user_id",
    "activities": "user_id",
    "expenses": "created_by",
}

class FormValidationError(ValueError):
    pass


def visible_fields(table, user):
    fields = TABLE_FIELDS[table]
    if user["role"] == "commercial":
        owner_field = OWNER_FIELDS.get(table)
        if owner_field:
            return tuple(field for field in fields if field.name != owner_field)
    return fields


def validate_form(table, form):
    fields = TABLE_FIELDS[table]
    result = {}
    errors = []
    for field in fields:
        raw = form.get(field.name, "")
        raw = str(raw).strip() if raw is not None else ""
        if field.kind == "checkbox":
            result[field.name] = raw.lower() in ("1", "true", "on", "yes")
            continue
        if not raw:
            if field.default is None:
                if field.required:
                    errors.append(f"{field.label} est obligatoire.")
                else:
                    result[field.name] = None
                continue
            raw = str(field.default)
        try:
            if field.kind == "select":
                if raw not in field.choices:
                    raise ValueError
                value = raw
            elif field.kind in ("integer", "foreign"):
                value = int(raw)
                if value < 0:
                    raise ValueError
                if field.kind == "foreign" and value == 0:
                    raise ValueError
            elif field.kind == "decimal":
                value = Decimal(raw)
                if not value.is_finite():
                    raise ValueError
                if field.minimum is not None and value < field.minimum:
                    raise ValueError
                if field.maximum is not None and value > field.maximum:
                    raise ValueError
            elif field.kind == "date":
                value = date.fromisoformat(raw)
            elif field.kind == "datetime":
                value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                value = raw
                if field.max_length is not None and len(value) > field.max_length:
                    raise ValueError
                if field.kind == "email" and not re.fullmatch(
                    r"[^@\s]+@[^@\s]+\.[^@\s]+", value
                ):
                    raise ValueError
        except (ValueError, InvalidOperation, OverflowError):
            errors.append(f"Valeur invalide pour « {field.label} ».")
            continue
        result[field.name] = value

    if table in ("contacts", "opportunities", "quotes"):
        has_prospect = result.get("prospect_id") is not None
        has_client = result.get("client_id") is not None
        if has_prospect == has_client:
            errors.append("Sélectionnez exactement un prospect ou un client.")
    elif table == "activities":
        if not any(result.get(key) is not None for key in (
            "prospect_id", "client_id", "opportunity_id", "contact_id"
        )):
            errors.append("Associez l’activité à au moins un élément CRM.")

    if table == "quotes" and result.get("issue_date") and result.get("valid_until"):
        if result["valid_until"] < result["issue_date"]:
            errors.append("La date de validité doit suivre la date d’émission.")
    if table == "invoices":
        if result.get("issue_date") and result.get("due_date") and (
            result["due_date"] < result["issue_date"]
        ):
            errors.append("L’échéance doit être égale ou postérieure à l’émission.")
    if errors:
        raise FormValidationError(" ".join(errors))
    return result


def form_values(table, row=None):
    row = row or {}
    result = {}
    for field in TABLE_FIELDS[table]:
        value = row.get(field.name)
        if value is None:
            result[field.name] = field.default if field.default is not None else ""
        elif isinstance(value, (date, datetime)):
            result[field.name] = value.strftime(
                "%Y-%m-%dT%H:%M" if field.kind == "datetime" else "%Y-%m-%d"
            )
        else:
            result[field.name] = str(value)
    return result


def validated_record_values(table, form, user):
    source = dict(form)
    if user["role"] == "commercial":
        owner_column = {
            "prospects": "assigned_user_id",
            "clients": "assigned_user_id",
            "opportunities": "assigned_user_id",
            "activities": "user_id",
            "expenses": "created_by",
        }.get(table)
        if owner_column:
            source[owner_column] = str(user["id"])
    return validate_form(table, source)
