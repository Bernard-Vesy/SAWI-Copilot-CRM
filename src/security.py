"""CSRF and role checks shared by public forms and CRM routes."""
import secrets

from fastapi import HTTPException, Request
from mysql.connector import Error as MySQLError
import logging

logger = logging.getLogger(__name__)
ROLES = ("admin", "commercial", "manager")


def csrf_token(request: Request):
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def require_csrf(request: Request, supplied: str):
    expected = request.session.get("csrf_token", "")
    if not expected or not secrets.compare_digest(expected, supplied or ""):
        raise HTTPException(status_code=403, detail="Jeton de formulaire invalide.")


def current_user(request: Request):
    user = request.session.get("crm_user")
    if not user or not user.get("id"):
        raise HTTPException(status_code=401, detail="Authentification requise.")
    # Refresh the role and active flag on every protected request so session
    # cookies cannot preserve revoked access or stale role assignments.
    from .database import DatabaseConfigurationError, fetch_one
    try:
        active = fetch_one(
            "SELECT id, first_name, last_name, email, role, is_active "
            "FROM users WHERE id = %s AND is_active = 1 LIMIT 1",
            (user["id"],),
        )
    except DatabaseConfigurationError:
        raise HTTPException(status_code=503, detail="La base CRM n’est pas configurée.")
    except MySQLError:
        logger.exception("CRM identity lookup failed")
        raise HTTPException(status_code=503, detail="La base CRM est inaccessible.")
    if not active or active["role"] not in ROLES:
        request.session.pop("crm_user", None)
        raise HTTPException(status_code=403, detail="Compte désactivé ou rôle invalide.")
    fresh_user = {
        "id": active["id"], "first_name": active["first_name"],
        "last_name": active["last_name"], "email": active["email"],
        "role": active["role"], "is_active": bool(active["is_active"]),
    }
    # Keep the signed, client-side session free of names, email, and role data.
    request.session["crm_user"] = {"id": active["id"]}
    return fresh_user


def roles_allowed(*roles):
    def dependency(request: Request):
        user = current_user(request)
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Accès non autorisé.")
        return user
    return dependency


def owner_predicate(user, column="assigned_user_id"):
    """Return a SQL fragment and values for role-aware data scoping."""
    if user["role"] in ("admin", "manager"):
        return "", ()
    return " WHERE " + column + " = %s", (user["id"],)
