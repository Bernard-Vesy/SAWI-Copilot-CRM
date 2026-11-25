import re
from decimal import Decimal
from contextlib import contextmanager

import pytest
from fastapi import HTTPException

from src import main
from src.crud import FormValidationError, validate_form
from src import database
from src.security import current_user


def _csrf(response):
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert match
    return match.group(1)


def test_prospect_validation_applies_schema_defaults_and_ranges():
    values = validate_form("prospects", {"company_name": "Exemple SA"})

    assert values["status"] == "new"
    assert values["country"] == "Suisse"
    assert values["potential_value"] == Decimal("0")
    assert values["conversion_probability"] == Decimal("0")

    with pytest.raises(FormValidationError, match="Probabilité"):
        validate_form("prospects", {
            "company_name": "Exemple SA",
            "conversion_probability": "101",
        })


def test_contact_must_belong_to_exactly_one_company():
    with pytest.raises(FormValidationError, match="exactement un"):
        validate_form("contacts", {
            "first_name": "Camille",
            "last_name": "Exemple",
        })
    with pytest.raises(FormValidationError, match="exactement un"):
        validate_form("contacts", {
            "prospect_id": "1",
            "client_id": "2",
            "first_name": "Camille",
            "last_name": "Exemple",
        })


def test_email_and_opportunity_probability_are_validated():
    with pytest.raises(FormValidationError, match="E-mail"):
        validate_form("prospects", {
            "company_name": "Exemple SA",
            "email": "pas-une-adresse",
        })
    with pytest.raises(FormValidationError, match="Probabilité"):
        validate_form("opportunities", {
            "title": "Projet fictif",
            "prospect_id": "12",
            "stage": "proposal",
            "probability": "-1",
        })


def test_commercial_prospect_creation_is_assigned_to_the_signed_in_user(client, monkeypatch):
    saved = {}
    user = {
        "id": 17,
        "first_name": "Camille",
        "last_name": "Exemple",
        "email": "camille@example.invalid",
        "role": "commercial",
        "is_active": True,
    }
    client.app.dependency_overrides[current_user] = lambda: user
    monkeypatch.setattr(
        main, "save_record",
        lambda table, record_id, values, *args: saved.update(
            table=table, record_id=record_id, values=values
        ) or 5,
    )
    try:
        page = client.get("/crm/prospects/new")
        response = client.post("/crm/prospects/new", data={
            "csrf_token": _csrf(page),
            "company_name": "Prospect Fictif SA",
            "assigned_user_id": "999",
        }, follow_redirects=False)
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 303
    assert saved["table"] == "prospects"
    assert saved["values"]["assigned_user_id"] == 17


def test_quote_item_save_calculates_line_and_parent_totals(monkeypatch):
    statements = []

    class Cursor:
        lastrowid = 23

        def execute(self, sql, params=()):
            statements.append((sql, params))

        def fetchone(self):
            return {"subtotal": Decimal("20.00"), "tax": Decimal("1.62")}

    class Connection:
        def commit(self):
            statements.append(("COMMIT", ()))

    @contextmanager
    def fake_cursor():
        yield Connection(), Cursor()

    monkeypatch.setattr(database, "db_cursor", fake_cursor)
    record_id = database.save_record("quote_items", None, {
        "quote_id": 41,
        "description": "Atelier fictif",
        "quantity": Decimal("2"),
        "unit_price": Decimal("10"),
        "tax_rate": Decimal("8.1"),
        "sort_order": 0,
    })

    insert = next(item for item in statements if item[0].startswith("INSERT INTO"))
    total_update = next(item for item in statements if item[0].startswith("UPDATE `quotes`"))
    assert record_id == 23
    assert insert[1][-1] == Decimal("21.62")
    assert total_update[1] == (
        Decimal("20.00"), Decimal("1.62"), Decimal("21.62"), 41
    )
    assert all("CREATE " not in sql.upper() for sql, _ in statements)


def test_commercial_cannot_create_catalog_services(client):
    user = {
        "id": 17,
        "first_name": "Camille",
        "last_name": "Exemple",
        "email": "camille@example.invalid",
        "role": "commercial",
        "is_active": True,
    }
    client.app.dependency_overrides[current_user] = lambda: user
    try:
        response = client.get("/crm/services/new")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 403
