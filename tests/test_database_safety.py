from contextlib import contextmanager

import pytest

from src import database
from src.config import Settings
from src.schema import TABLES


def settings(**overrides):
    values = dict(
        app_env="test", port=8000, database_enabled=False, db_host="", db_port="",
        db_name="", db_user="", db_password="", db_tls_mode="", db_tls_ca="",
        session_secret="", entra_tenant_id="", entra_client_id="",
        entra_client_secret="", entra_redirect_uri="",
    )
    values.update(overrides)
    return Settings(**values)


def test_missing_database_settings_fail_before_connector_call(monkeypatch):
    monkeypatch.setattr(database, "settings", settings())
    monkeypatch.setattr(
        database.connector, "connect",
        lambda **kwargs: pytest.fail("No network/database connection is allowed"),
    )
    with pytest.raises(database.DatabaseConfigurationError, match="DATABASE_ENABLED"):
        database.connection_options()


def test_enabled_database_requires_explicit_host_credentials_and_tls(monkeypatch):
    monkeypatch.setattr(database, "settings", settings(database_enabled=True))
    with pytest.raises(database.DatabaseConfigurationError) as error:
        database.connection_options()
    message = str(error.value)
    assert (
        "DB_HOST" in message and "DB_PORT" in message
        and "DB_PASSWORD" in message and "DB_TLS_MODE" in message
    )
    assert "secret" not in message.lower()


def test_tls_configuration_is_explicit(monkeypatch):
    monkeypatch.setattr(database, "settings", settings(
        database_enabled=True, db_host="db.test.invalid", db_port=3306,
        db_name="clairia_crm",
        db_user="test_user", db_password="synthetic-only", db_tls_mode="verify_identity",
        db_tls_ca="C:/test/ca.pem",
    ))
    options = database.connection_options()
    assert options["ssl_verify_cert"] is True
    assert options["ssl_verify_identity"] is True
    assert options["ssl_ca"] == "C:/test/ca.pem"
    assert options["connection_timeout"] == 5


def test_production_rejects_disabled_database_tls(monkeypatch):
    monkeypatch.setattr(database, "settings", settings(
        app_env="production", database_enabled=True, db_host="db.example.invalid",
        db_port=3306, db_name="clairia_crm", db_user="test_user",
        db_password="synthetic-only", db_tls_mode="disabled",
    ))

    with pytest.raises(database.DatabaseConfigurationError, match="cannot be disabled"):
        database.connection_options()


def test_website_insert_binds_all_user_values(monkeypatch):
    calls = {}
    class Cursor:
        lastrowid = 5
        def execute(self, sql, params):
            calls["sql"], calls["params"] = sql, params
    class Connection:
        def commit(self):
            calls["committed"] = True
    @contextmanager
    def cursor(*args, **kwargs):
        yield Connection(), Cursor()

    monkeypatch.setattr(database, "db_cursor", cursor)
    value = "test@example.invalid'); DROP TABLE users; --"
    result = database.insert_website_request({
        "first_name": "Test", "last_name": "Fictif", "email": value,
        "request_type": "contact",
    })
    assert result == 5
    assert value in calls["params"]
    assert value not in calls["sql"]
    assert "INSERT INTO website_requests" in calls["sql"]
    assert calls["committed"]


def test_full_existing_table_inventory_and_constraints_are_documented():
    assert set(TABLES) == {
        "users", "prospects", "clients", "contacts", "services", "opportunities",
        "activities", "quotes", "quote_items", "invoices", "invoice_items",
        "expenses", "website_requests",
    }
    assert TABLES["users"].schema_notes[0] == "id INT PRIMARY KEY AUTO_INCREMENT"
    assert "exactly one of prospect_id/client_id is non-NULL" in TABLES["contacts"].constraints
    assert "amount_paid <= total_amount" in TABLES["invoices"].constraints
    assert "quote_id -> quotes ON DELETE CASCADE" in TABLES["quote_items"].foreign_keys
    assert "assigned_user_id -> users ON DELETE SET NULL" in TABLES["prospects"].foreign_keys
