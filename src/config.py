"""Environment-backed configuration. No secrets or DB connections are implicit."""
from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_env: str
    port: int
    database_enabled: bool
    db_host: str
    db_port: int | str
    db_name: str
    db_user: str
    db_password: str
    db_tls_mode: str
    db_tls_ca: str
    session_secret: str
    entra_tenant_id: str
    entra_client_id: str
    entra_client_secret: str
    entra_redirect_uri: str

    @classmethod
    def from_env(cls):
        raw_db_port = os.getenv("DB_PORT", "").strip()
        try:
            db_port = int(raw_db_port)
        except ValueError:
            db_port = raw_db_port
        return cls(
            app_env=os.getenv("APP_ENV", "development").strip().lower(),
            port=int(os.getenv("PORT", "8000")),
            database_enabled=os.getenv("DATABASE_ENABLED", "false").strip().lower() == "true",
            db_host=os.getenv("DB_HOST", "").strip(),
            db_port=db_port,
            db_name=os.getenv("DB_NAME", "").strip(),
            db_user=os.getenv("DB_USER", "").strip(),
            db_password=os.getenv("DB_PASSWORD", ""),
            db_tls_mode=os.getenv("DB_TLS_MODE", "").strip().lower(),
            db_tls_ca=os.getenv("DB_TLS_CA", "").strip(),
            session_secret=os.getenv("SESSION_SECRET", "").strip(),
            entra_tenant_id=os.getenv("ENTRA_TENANT_ID", "").strip(),
            entra_client_id=os.getenv("ENTRA_CLIENT_ID", "").strip(),
            entra_client_secret=os.getenv("ENTRA_CLIENT_SECRET", ""),
            entra_redirect_uri=os.getenv(
                "ENTRA_REDIRECT_URI", "http://localhost:8000/auth/callback"
            ).strip(),
        )

    def database_problems(self):
        if not self.database_enabled:
            return ["DATABASE_ENABLED is false"]
        missing = [
            name for name, value in (
                ("DB_HOST", self.db_host),
                ("DB_PORT", self.db_port),
                ("DB_NAME", self.db_name),
                ("DB_USER", self.db_user),
                ("DB_PASSWORD", self.db_password),
                ("DB_TLS_MODE", self.db_tls_mode),
            ) if not value or (
                isinstance(value, str) and value.startswith("<")
            )
        ]
        try:
            parsed_port = int(self.db_port)
            if not 1 <= parsed_port <= 65535:
                missing.append("DB_PORT must be between 1 and 65535")
        except (TypeError, ValueError):
            missing.append("DB_PORT must be a valid port number")
        if self.db_tls_mode not in ("verify_identity", "verify_ca", "disabled"):
            missing.append("DB_TLS_MODE must be verify_identity, verify_ca, or disabled")
        if self.app_env == "production" and self.db_tls_mode == "disabled":
            missing.append("DB_TLS_MODE cannot be disabled in production")
        if self.db_tls_mode in ("verify_identity", "verify_ca") and (
            not self.db_tls_ca or self.db_tls_ca.startswith("<")
        ):
            missing.append("DB_TLS_CA is required for the selected TLS mode")
        return missing


settings = Settings.from_env()
