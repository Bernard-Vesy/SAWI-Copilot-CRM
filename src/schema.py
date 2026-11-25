"""Documentation-level map of the pre-existing MySQL schema.

This module describes the user's supplied schema; it is deliberately not ORM
metadata and has no create/alter/migration behavior.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TableSpec:
    columns: tuple
    enums: dict
    constraints: tuple = ()
    foreign_keys: tuple = ()
    indexes: tuple = ()
    id_type: str = "INT PRIMARY KEY AUTO_INCREMENT"

    @property
    def schema_notes(self):
        """Include the common primary key without inventing unspecified SQL sizes."""
        return ("id " + self.id_type,) + self.constraints


TABLES = {
    "users": TableSpec(
        ("id", "first_name", "last_name", "email", "password_hash", "role",
         "is_active", "created_at", "updated_at"),
        {"role": ("admin", "commercial", "manager")},
        ("UNIQUE(email)", "password_hash NULL", "role DEFAULT commercial"),
    ),
    "prospects": TableSpec(
        ("id", "company_name", "contact_name", "email", "phone", "website",
         "industry", "company_size", "address", "postal_code", "city", "canton",
         "country", "source", "status", "potential_value",
         "conversion_probability", "assigned_user_id", "notes", "created_at",
         "updated_at"),
        {"status": ("new", "contacted", "qualified", "converted", "lost")},
        ("company_name NOT NULL", "potential_value >= 0 DEFAULT 0",
         "conversion_probability BETWEEN 0 AND 100 DEFAULT 0",
         "country DEFAULT Suisse"),
        ("assigned_user_id -> users ON DELETE SET NULL",),
        ("status", "canton", "source", "industry", "created_at"),
    ),
    "clients": TableSpec(
        ("id", "prospect_id", "company_name", "industry", "company_size", "email",
         "phone", "address", "postal_code", "city", "canton", "country",
         "vat_number", "status", "assigned_user_id", "customer_since", "notes",
         "created_at", "updated_at"),
        {"status": ("active", "inactive", "lost")},
        ("company_name NOT NULL", "UNIQUE(prospect_id)", "country DEFAULT Suisse"),
        ("prospect_id -> prospects ON DELETE RESTRICT",
         "assigned_user_id -> users ON DELETE SET NULL"),
        ("status", "canton", "industry"),
    ),
    "contacts": TableSpec(
        ("id", "prospect_id", "client_id", "first_name", "last_name", "job_title",
         "email", "phone", "mobile", "is_primary", "notes", "created_at",
         "updated_at"),
        {},
        ("first_name NOT NULL", "last_name NOT NULL",
         "exactly one of prospect_id/client_id is non-NULL"),
        ("prospect_id -> prospects ON DELETE RESTRICT",
         "client_id -> clients ON DELETE RESTRICT"),
        ("email", "prospect_id", "client_id"),
    ),
    "services": TableSpec(
        ("id", "code", "name", "description", "category", "pricing_model",
         "unit_price", "currency", "estimated_duration", "is_active",
         "created_at", "updated_at"),
        {"pricing_model": ("fixed", "hourly", "daily", "subscription")},
        ("UNIQUE(code)", "name NOT NULL", "unit_price >= 0 DEFAULT 0",
         "currency DEFAULT CHF"),
        indexes=("category",),
    ),
    "opportunities": TableSpec(
        ("id", "prospect_id", "client_id", "title", "description", "service_id",
         "estimated_value", "probability", "stage", "expected_close_date",
         "actual_close_date", "assigned_user_id", "loss_reason", "created_at",
         "updated_at"),
        {"stage": ("qualification", "discovery", "proposal", "negotiation", "won", "lost")},
        ("title NOT NULL", "exactly one of prospect_id/client_id is non-NULL",
         "estimated_value >= 0 DEFAULT 0", "probability BETWEEN 0 AND 100 DEFAULT 0"),
        ("prospect_id -> prospects ON DELETE RESTRICT",
         "client_id -> clients ON DELETE RESTRICT",
         "service_id -> services ON DELETE SET NULL",
         "assigned_user_id -> users ON DELETE SET NULL"),
        ("stage", "expected_close_date", "service_id"),
    ),
    "activities": TableSpec(
        ("id", "prospect_id", "client_id", "opportunity_id", "contact_id",
         "user_id", "activity_type", "subject", "description", "status",
         "due_date", "completed_at", "created_at", "updated_at"),
        {"activity_type": ("call", "email", "meeting", "task", "demo", "other"),
         "status": ("planned", "completed", "cancelled")},
        ("user_id NOT NULL", "subject NOT NULL",
         "at least one of prospect_id/client_id/opportunity_id/contact_id is non-NULL"),
        ("prospect_id -> prospects", "client_id -> clients",
         "opportunity_id -> opportunities", "contact_id -> contacts",
         "user_id -> users ON DELETE RESTRICT"),
        ("activity_type", "status", "due_date"),
    ),
    "quotes": TableSpec(
        ("id", "quote_number", "prospect_id", "client_id", "opportunity_id",
         "issue_date", "valid_until", "status", "subtotal", "tax_amount",
         "total_amount", "tax_rate", "currency", "notes", "created_at", "updated_at"),
        {"status": ("draft", "sent", "accepted", "rejected", "expired")},
        ("UNIQUE(quote_number)", "exactly one of prospect_id/client_id is non-NULL",
         "issue_date NOT NULL", "subtotal/tax_amount/total_amount >= 0",
         "tax_rate BETWEEN 0 AND 100", "currency DEFAULT CHF"),
        ("prospect_id -> prospects ON DELETE RESTRICT",
         "client_id -> clients ON DELETE RESTRICT",
         "opportunity_id -> opportunities"),
    ),
    "quote_items": TableSpec(
        ("id", "quote_id", "service_id", "description", "quantity", "unit_price",
         "tax_rate", "line_total", "sort_order"),
        {},
        ("quote_id NOT NULL", "description NOT NULL", "quantity > 0",
         "unit_price >= 0", "tax_rate BETWEEN 0 AND 100", "line_total >= 0"),
        ("quote_id -> quotes ON DELETE CASCADE",
         "service_id -> services ON DELETE SET NULL"),
    ),
    "invoices": TableSpec(
        ("id", "invoice_number", "client_id", "quote_id", "issue_date", "due_date",
         "payment_date", "status", "subtotal", "tax_amount", "total_amount",
         "amount_paid", "currency", "notes", "created_at", "updated_at"),
        {"status": ("draft", "sent", "partially_paid", "paid", "overdue", "cancelled")},
        ("invoice_number UNIQUE", "client_id NOT NULL", "issue_date/due_date NOT NULL",
         "subtotal/tax_amount/total_amount/amount_paid >= 0",
         "amount_paid <= total_amount", "currency DEFAULT CHF"),
        ("client_id -> clients ON DELETE RESTRICT",
         "quote_id -> quotes ON DELETE RESTRICT"),
    ),
    "invoice_items": TableSpec(
        ("id", "invoice_id", "service_id", "description", "quantity", "unit_price",
         "tax_rate", "line_total", "sort_order"),
        {},
        ("invoice_id NOT NULL", "description NOT NULL", "quantity > 0",
         "unit_price >= 0", "tax_rate BETWEEN 0 AND 100", "line_total >= 0"),
        ("invoice_id -> invoices ON DELETE CASCADE",
         "service_id -> services ON DELETE SET NULL"),
    ),
    "expenses": TableSpec(
        ("id", "expense_date", "category", "supplier", "description", "amount",
         "tax_amount", "total_amount", "currency", "payment_status", "payment_date",
         "created_by", "created_at", "updated_at"),
        {"payment_status": ("pending", "paid")},
        ("expense_date/category NOT NULL", "amount/tax_amount/total_amount >= 0",
         "currency DEFAULT CHF"),
        ("created_by -> users ON DELETE SET NULL",),
        ("expense_date", "category", "payment_status"),
    ),
    "website_requests": TableSpec(
        ("id", "company_name", "first_name", "last_name", "email", "phone",
         "request_type", "message", "preferred_date", "status", "prospect_id",
         "created_at"),
        {"request_type": ("contact", "diagnostic", "appointment"),
         "status": ("new", "processed", "closed")},
        ("first_name/last_name/email NOT NULL",),
        ("prospect_id -> prospects ON DELETE RESTRICT",),
        ("status", "created_at", "email"),
    ),
}

QUOTE_ITEM_COLUMNS = TABLES["quote_items"].columns
INVOICE_ITEM_COLUMNS = TABLES["invoice_items"].columns

# Types and defaults stated in the supplied schema summary. Exact VARCHAR lengths
# and DECIMAL precision were not included there and are intentionally not guessed.
KNOWN_TYPES = {
    "id": "INT PRIMARY KEY AUTO_INCREMENT",
    "potential_value": "DECIMAL NOT NULL DEFAULT 0 CHECK >= 0",
    "conversion_probability": "DECIMAL NOT NULL DEFAULT 0 CHECK 0..100",
    "estimated_value": "DECIMAL NOT NULL DEFAULT 0 CHECK >= 0",
    "probability": "DECIMAL NOT NULL DEFAULT 0 CHECK 0..100",
    "unit_price": "DECIMAL NOT NULL DEFAULT 0 CHECK >= 0",
    "tax_rate": "DECIMAL CHECK 0..100",
    "quantity": "DECIMAL CHECK > 0",
    "line_total": "DECIMAL CHECK >= 0",
    "amount_paid": "DECIMAL CHECK >= 0 AND <= total_amount",
    "currency": "CHARACTER, DEFAULT CHF",
    "country": "CHARACTER, DEFAULT Suisse",
}
