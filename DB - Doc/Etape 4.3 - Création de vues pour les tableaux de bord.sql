CREATE OR REPLACE VIEW vw_sales_pipeline AS

SELECT
    o.id,
    o.title,
    o.stage,
    o.estimated_value,
    o.probability,

    ROUND(
        o.estimated_value * o.probability / 100,
        2
    ) AS weighted_value,

    o.expected_close_date,

    COALESCE(
        p.company_name,
        c.company_name
    ) AS company_name,

    s.name AS service_name,

    CONCAT(
        u.first_name,
        ' ',
        u.last_name
    ) AS sales_owner

FROM opportunities o

LEFT JOIN prospects p
    ON o.prospect_id = p.id

LEFT JOIN clients c
    ON o.client_id = c.id

LEFT JOIN services s
    ON o.service_id = s.id

LEFT JOIN users u
    ON o.assigned_user_id = u.id;