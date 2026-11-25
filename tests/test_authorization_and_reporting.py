from decimal import Decimal

import pytest
from starlette.requests import Request

from src.reporting import average_deal_size, conversion_rate, overview_queries, weighted_pipeline
from src.security import current_user, owner_predicate


def user(role, user_id=7):
    return {"id": user_id, "role": role}


def test_commercial_queries_are_scoped_to_assigned_records():
    sql, params = overview_queries(user("commercial"))["opportunities"]
    assert "assigned_user_id = %s" in sql
    assert params == (7,)
    revenue_sql, revenue_params = overview_queries(user("commercial"))["revenue"]
    assert "JOIN clients" in revenue_sql
    assert revenue_params == (7,)


def test_manager_and_admin_reporting_is_not_limited_to_owner():
    for role in ("admin", "manager"):
        sql, params = overview_queries(user(role))["opportunities"]
        assert "assigned_user_id" not in sql
        assert params == ()


def test_owner_predicate_has_bound_parameter():
    sql, params = owner_predicate(user("commercial", 41), "assigned_user_id")
    assert sql == " WHERE assigned_user_id = %s"
    assert params == (41,)
    assert owner_predicate(user("manager"), "assigned_user_id") == ("", ())


def test_current_user_refreshes_role_from_active_database_user(monkeypatch):
    from src import database

    monkeypatch.setattr(database, "fetch_one", lambda _sql, _params: {
        "id": 7, "first_name": "Test", "last_name": "Fictif",
        "email": "test@example.invalid", "role": "manager", "is_active": 1,
    })
    request = Request({
        "type": "http", "method": "GET", "path": "/crm", "headers": [],
        "session": {"crm_user": {"id": 7, "role": "commercial", "is_active": True}},
    })
    active_user = current_user(request)
    assert active_user["role"] == "manager"
    assert request.session["crm_user"] == {"id": 7}


def test_current_user_rejects_inactive_database_user(monkeypatch):
    from fastapi import HTTPException
    from src import database

    monkeypatch.setattr(database, "fetch_one", lambda _sql, _params: None)
    request = Request({
        "type": "http", "method": "GET", "path": "/crm", "headers": [],
        "session": {"crm_user": {"id": 7, "role": "commercial", "is_active": True}},
    })
    with pytest.raises(HTTPException) as error:
        current_user(request)
    assert error.value.status_code == 403
    assert "crm_user" not in request.session


def test_weighted_pipeline_excludes_closed_stages():
    assert weighted_pipeline([
        {"estimated_value": "1000.00", "probability": 50, "stage": "proposal"},
        {"estimated_value": "300", "probability": 20, "stage": "won"},
        {"estimated_value": "700", "probability": 25, "stage": "discovery"},
    ]) == Decimal("675.00")


def test_report_math_handles_empty_and_zero_values():
    assert conversion_rate(0, 0) == 0.0
    assert conversion_rate(2, 8) == 25.0
    assert average_deal_size([]) == Decimal("0")
    assert average_deal_size([1200, 800]) == Decimal("1000")
