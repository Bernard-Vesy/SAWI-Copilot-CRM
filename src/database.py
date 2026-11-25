"""Small parameterized MySQL access layer; never creates or migrates schema."""
from contextlib import contextmanager
from decimal import Decimal, ROUND_HALF_UP

from mysql import connector

from .config import settings


class DatabaseConfigurationError(RuntimeError):
    pass


def connection_options():
    problems = settings.database_problems()
    if problems:
        # Never include DB_PASSWORD in errors or logs.
        raise DatabaseConfigurationError("; ".join(problems))
    opts = {
        "host": settings.db_host,
        "port": int(settings.db_port),
        "database": settings.db_name,
        "user": settings.db_user,
        "password": settings.db_password,
        "connection_timeout": 5,
        "autocommit": False,
    }
    if settings.db_tls_mode == "disabled":
        opts["ssl_disabled"] = True
    else:
        opts.update({
            "ssl_ca": settings.db_tls_ca,
            "ssl_verify_cert": True,
            "ssl_verify_identity": settings.db_tls_mode == "verify_identity",
        })
    return opts


@contextmanager
def db_cursor(dictionary=True):
    connection = connector.connect(**connection_options())
    cursor = None
    try:
        cursor = connection.cursor(dictionary=dictionary)
        yield connection, cursor
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def fetch_all(sql, params=()):
    with db_cursor() as (_, cursor):
        cursor.execute(sql, params)
        return cursor.fetchall()


def fetch_one(sql, params=()):
    with db_cursor() as (_, cursor):
        cursor.execute(sql, params)
        return cursor.fetchone()


def check_connection():
    with db_cursor() as (_, cursor):
        cursor.execute("SELECT 1")
        cursor.fetchone()


def insert_website_request(values):
    sql = (
        "INSERT INTO website_requests "
        "(company_name, first_name, last_name, email, phone, request_type, "
        "message, preferred_date, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'new')"
    )
    with db_cursor(dictionary=False) as (connection, cursor):
        cursor.execute(sql, (
            values.get("company_name") or None,
            values["first_name"],
            values["last_name"],
            values["email"],
            values.get("phone") or None,
            values["request_type"],
            values.get("message") or None,
            values.get("preferred_date") or None,
        ))
        connection.commit()
        return cursor.lastrowid


def fetch_record(table, record_id, scope_sql="", scope_params=()):
    from .crud import TABLE_FIELDS

    if table not in TABLE_FIELDS:
        raise ValueError("Unknown CRM table.")
    columns = ["id"] + [field.name for field in TABLE_FIELDS[table]]
    sql = (
        "SELECT " + ", ".join("`" + column + "`" for column in columns) +
        " FROM `" + table + "` WHERE `id` = %s" + scope_sql + " LIMIT 1"
    )
    with db_cursor() as (_, cursor):
        cursor.execute(sql, (record_id,) + tuple(scope_params))
        return cursor.fetchone()


def _update_item_totals(cursor, parent_table, parent_column, parent_id):
    item_table = {"quotes": "quote_items", "invoices": "invoice_items"}[parent_table]
    cursor.execute(
        "SELECT ROUND(COALESCE(SUM(quantity * unit_price), 0), 2) AS subtotal, "
        "ROUND(COALESCE(SUM(quantity * unit_price * tax_rate / 100), 0), 2) AS tax "
        "FROM `" + item_table + "` "
        "WHERE `" + parent_column + "` = %s",
        (parent_id,),
    )
    totals = cursor.fetchone()
    cursor.execute(
        "UPDATE `" + parent_table + "` SET subtotal = %s, tax_amount = %s, "
        "total_amount = %s WHERE id = %s",
        (totals["subtotal"], totals["tax"], totals["subtotal"] + totals["tax"],
         parent_id),
    )


def save_record(table, record_id, values, scope_sql="", scope_params=()):
    """Insert or update allowlisted business fields without schema changes."""
    from .crud import TABLE_FIELDS

    if table not in TABLE_FIELDS:
        raise ValueError("Unknown CRM table.")
    allowed = {field.name for field in TABLE_FIELDS[table]}
    computed_columns = {
        "expenses": {"total_amount"},
        "quote_items": {"line_total"},
        "invoice_items": {"line_total"},
    }.get(table, set())
    if not values or not set(values).issubset(allowed | computed_columns):
        raise ValueError("Invalid CRM fields.")

    values = dict(values)
    if table == "expenses":
        values["total_amount"] = (
            Decimal(str(values["amount"])) + Decimal(str(values["tax_amount"]))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if table in ("quote_items", "invoice_items"):
        quantity = Decimal(str(values["quantity"]))
        unit_price = Decimal(str(values["unit_price"]))
        tax_rate = Decimal(str(values.get("tax_rate") or 0))
        values["line_total"] = (
            quantity * unit_price * (Decimal("1") + tax_rate / Decimal("100"))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    with db_cursor() as (connection, cursor):
        old_parent_id = None
        if record_id is not None:
            cursor.execute(
                "SELECT * FROM `" + table + "` WHERE id = %s" + scope_sql + " LIMIT 1",
                (record_id,) + tuple(scope_params),
            )
            previous = cursor.fetchone()
            if not previous:
                return None
            if table == "quote_items":
                old_parent_id = previous["quote_id"]
            elif table == "invoice_items":
                old_parent_id = previous["invoice_id"]
            assignments = ", ".join("`" + name + "` = %s" for name in values)
            cursor.execute(
                "UPDATE `" + table + "` SET " + assignments +
                " WHERE id = %s" + scope_sql,
                tuple(values.values()) + (record_id,) + tuple(scope_params),
            )
            saved_id = record_id
        else:
            columns = tuple(values)
            placeholders = ", ".join("%s" for _ in columns)
            cursor.execute(
                "INSERT INTO `" + table + "` (" +
                ", ".join("`" + name + "`" for name in columns) +
                ") VALUES (" + placeholders + ")",
                tuple(values[name] for name in columns),
            )
            saved_id = cursor.lastrowid

        if table == "quote_items":
            parent_id = values["quote_id"]
            _update_item_totals(cursor, "quotes", "quote_id", parent_id)
            if old_parent_id and old_parent_id != parent_id:
                _update_item_totals(cursor, "quotes", "quote_id", old_parent_id)
        elif table == "invoice_items":
            parent_id = values["invoice_id"]
            _update_item_totals(cursor, "invoices", "invoice_id", parent_id)
            if old_parent_id and old_parent_id != parent_id:
                _update_item_totals(cursor, "invoices", "invoice_id", old_parent_id)

        connection.commit()
        return saved_id
