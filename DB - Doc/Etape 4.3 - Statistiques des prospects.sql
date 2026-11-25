CREATE OR REPLACE VIEW vw_prospect_statistics AS

SELECT
    canton,
    industry,
    source,
    status,

    COUNT(*) AS prospect_count,

    SUM(potential_value) AS total_potential_value,

    AVG(conversion_probability) AS avg_conversion_probability

FROM prospects

GROUP BY
    canton,
    industry,
    source,
    status;