"""Pure helpers for reports calculated from the existing tables (no SQL views)."""
from decimal import Decimal


def weighted_pipeline(rows):
    return sum(
        (Decimal(str(row.get("estimated_value") or 0)) *
         Decimal(str(row.get("probability") or 0)) / Decimal("100")
         for row in rows if row.get("stage") not in ("won", "lost")),
        Decimal("0"),
    )


def conversion_rate(converted, total):
    return round((converted / total) * 100, 1) if total else 0.0


def average_deal_size(won_values):
    values = [Decimal(str(value or 0)) for value in won_values]
    return sum(values, Decimal("0")) / len(values) if values else Decimal("0")


def overview_queries(user):
    if user["role"] == "commercial":
        where = " WHERE assigned_user_id = %s"
        args = (user["id"],)
        invoice_scope = (
            "JOIN clients c ON c.id = i.client_id WHERE c.assigned_user_id = %s AND "
        )
        invoice_args = (user["id"],)
    else:
        where, args = "", ()
        invoice_scope = "WHERE "
        invoice_args = ()
    if user["role"] == "commercial":
        revenue_sql = (
            "SELECT COALESCE(SUM(i.total_amount), 0) AS revenue FROM invoices i "
            "JOIN clients c ON c.id = i.client_id WHERE c.assigned_user_id = %s "
            "AND i.status IN ('sent', 'partially_paid', 'paid', 'overdue')"
        )
        revenue_args = (user["id"],)
    else:
        revenue_sql = (
            "SELECT COALESCE(SUM(total_amount), 0) AS revenue FROM invoices "
            "WHERE status IN ('sent', 'partially_paid', 'paid', 'overdue')"
        )
        revenue_args = ()
    if user["role"] == "commercial":
        owner_sql = (
            "SELECT u.first_name, u.last_name, "
            "COALESCE(SUM(o.estimated_value * o.probability / 100), 0) AS weighted "
            "FROM opportunities o JOIN users u ON u.id = o.assigned_user_id "
            "WHERE o.assigned_user_id = %s AND o.stage NOT IN ('won', 'lost') "
            "GROUP BY u.id, u.first_name, u.last_name ORDER BY weighted DESC LIMIT 8"
        )
        owner_args = (user["id"],)
    else:
        owner_sql = (
            "SELECT u.first_name, u.last_name, "
            "COALESCE(SUM(o.estimated_value * o.probability / 100), 0) AS weighted "
            "FROM opportunities o JOIN users u ON u.id = o.assigned_user_id "
            "WHERE o.stage NOT IN ('won', 'lost') "
            "GROUP BY u.id, u.first_name, u.last_name ORDER BY weighted DESC LIMIT 8"
        )
        owner_args = ()
    return {
        "opportunities": (
            "SELECT stage, COUNT(*) AS count, COALESCE(SUM(estimated_value), 0) AS value "
            "FROM opportunities" + where + " GROUP BY stage ORDER BY stage", args),
        "prospects": (
            "SELECT status, COUNT(*) AS count FROM prospects" + where +
            " GROUP BY status ORDER BY status", args),
        "pipeline": (
            "SELECT COALESCE(SUM(estimated_value * probability / 100), 0) AS weighted "
            "FROM opportunities" + where +
            (" AND" if where else " WHERE") + " stage NOT IN ('won', 'lost')", args),
        "revenue": (revenue_sql, revenue_args),
        "new_prospects": (
            "SELECT COUNT(*) AS count FROM prospects" + where +
            (" AND" if where else " WHERE") +
            " created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)", args),
        "conversion": (
            "SELECT COUNT(*) AS total, "
            "COALESCE(SUM(status = 'converted'), 0) AS converted FROM prospects" + where,
            args),
        "average_deal": (
            "SELECT COALESCE(AVG(estimated_value), 0) AS average FROM opportunities" +
            where + (" AND" if where else " WHERE") + " stage = 'won'", args),
        "by_canton": (
            "SELECT canton AS label, COUNT(*) AS count FROM prospects" + where +
            (" AND" if where else " WHERE") +
            " canton IS NOT NULL AND canton <> '' GROUP BY canton ORDER BY count DESC LIMIT 8",
            args),
        "by_source": (
            "SELECT source AS label, COUNT(*) AS count FROM prospects" + where +
            (" AND" if where else " WHERE") +
            " source IS NOT NULL AND source <> '' GROUP BY source ORDER BY count DESC LIMIT 8",
            args),
        "by_service": (
            "SELECT s.name AS label, COUNT(*) AS count, "
            "COALESCE(SUM(o.estimated_value), 0) AS value "
            "FROM opportunities o LEFT JOIN services s ON s.id = o.service_id" +
            (" WHERE o.assigned_user_id = %s" if user["role"] == "commercial" else "") +
            " GROUP BY s.name ORDER BY value DESC LIMIT 8", args),
        "monthly_revenue": (
            "SELECT DATE_FORMAT(i.issue_date, '%Y-%m') AS label, "
            "SUM(i.total_amount) AS value FROM invoices i " + invoice_scope +
            "i.status IN ('sent', 'partially_paid', 'paid', 'overdue') "
            "GROUP BY DATE_FORMAT(i.issue_date, '%Y-%m') ORDER BY label DESC LIMIT 12",
            invoice_args),
        "pipeline_by_owner": (owner_sql, owner_args),
    }
