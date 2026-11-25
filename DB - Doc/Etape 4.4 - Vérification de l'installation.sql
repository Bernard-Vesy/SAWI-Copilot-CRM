USE clairia_crm;

-- Afficher les tables et vues
SHOW FULL TABLES;

-- Vérifier le catalogue
SELECT * FROM services;

-- Vérifier les contraintes
SELECT
    TABLE_NAME,
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE
FROM information_schema.TABLE_CONSTRAINTS
WHERE TABLE_SCHEMA = 'clairia_crm';

-- Compter les services
SELECT COUNT(*) AS nombre_services
FROM services;