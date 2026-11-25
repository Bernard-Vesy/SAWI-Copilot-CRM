CREATE OR REPLACE VIEW vw_monthly_revenue AS

SELECT
    YEAR(issue_date) AS revenue_year,
    MONTH(issue_date) AS revenue_month,

    COUNT(*) AS invoice_count,

    SUM(subtotal) AS revenue_excluding_tax,

    SUM(tax_amount) AS tax_total,

    SUM(total_amount) AS revenue_including_tax,

    SUM(amount_paid) AS collected_amount

FROM invoices

WHERE status NOT IN (
    'draft',
    'cancelled'
)

GROUP BY
    YEAR(issue_date),
    MONTH(issue_date);