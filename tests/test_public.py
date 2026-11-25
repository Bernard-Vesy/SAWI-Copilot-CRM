import re

from src import main
from src.database import DatabaseConfigurationError


def csrf_from(response):
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert match
    return match.group(1)


def test_health_endpoints_do_not_require_database(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json()["database"] in (
        "not_configured", "ready", "configuration_incomplete"
    )


def test_public_pages_render_in_french(client):
    for path in ("/", "/services", "/a-propos", "/contact", "/login"):
        response = client.get(path)
        assert response.status_code == 200
        assert 'lang="fr"' in response.text


def test_public_request_uses_parameterized_write_and_synthetic_values(client, monkeypatch):
    saved = {}

    def fake_insert(values):
        saved.update(values)
        return 12

    monkeypatch.setattr(main, "insert_website_request", fake_insert)
    page = client.get("/contact")
    response = client.post("/contact", data={
        "csrf_token": csrf_from(page),
        "first_name": "Camille",
        "last_name": "Exemple",
        "email": "camille@example.invalid",
        "company_name": "Atelier Fictif SA",
        "request_type": "diagnostic",
        "message": "Données synthétiques pour le test.",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/contact?sent=true"
    assert saved["email"] == "camille@example.invalid"
    assert saved["request_type"] == "diagnostic"


def test_contact_reports_missing_database_without_recording(client, monkeypatch):
    def unavailable(_values):
        raise DatabaseConfigurationError("DATABASE_ENABLED is false")

    monkeypatch.setattr(main, "insert_website_request", unavailable)
    page = client.get("/contact")
    response = client.post("/contact", data={
        "csrf_token": csrf_from(page), "first_name": "Test", "last_name": "Fictif",
        "email": "test@example.invalid", "request_type": "contact",
    })
    assert response.status_code == 503
    assert "Votre demande n’a pas été enregistrée" in response.text


def test_contact_rejects_bad_csrf_and_invalid_request_type(client):
    page = client.get("/contact")
    bad_csrf = client.post("/contact", data={
        "csrf_token": "wrong", "first_name": "Test", "last_name": "Fictif",
        "email": "test@example.invalid", "request_type": "contact",
    })
    assert bad_csrf.status_code == 403
    bad_type = client.post("/contact", data={
        "csrf_token": csrf_from(page), "first_name": "Test", "last_name": "Fictif",
        "email": "test@example.invalid", "request_type": "unsupported",
    })
    assert bad_type.status_code == 422


def test_crm_requires_authenticated_session(client):
    assert client.get("/crm", follow_redirects=False).status_code == 401
    assert client.get("/crm/prospects", follow_redirects=False).status_code == 401
