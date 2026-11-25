-- ============================================================
-- INITIALISATION DES SERVICES CLAIRIA
-- ============================================================

INSERT INTO services (
    code,
    name,
    description,
    category,
    pricing_model,
    unit_price,
    currency,
    estimated_duration
)
VALUES

(
    'SRV001',
    'Diagnostic découverte IA',
    'Identification des opportunités d utilisation de Microsoft Copilot et de l automatisation dans une PME.',
    'Diagnostic',
    'fixed',
    0.00,
    'CHF',
    '1 à 2 jours'
),

(
    'SRV002',
    'Audit Copilot et feuille de route',
    'Analyse des processus, de la maturité numérique et des opportunités IA avec élaboration d une feuille de route.',
    'Conseil',
    'fixed',
    0.00,
    'CHF',
    '2 à 3 semaines'
),

(
    'SRV003',
    'Formation Microsoft Copilot',
    'Formation pratique destinée aux collaborateurs et dirigeants pour exploiter efficacement Microsoft Copilot.',
    'Formation',
    'daily',
    0.00,
    'CHF',
    '1 journée'
),

(
    'SRV004',
    'Prototype et automatisation',
    'Conception et réalisation d un premier processus automatisé avec les technologies Microsoft.',
    'Automatisation',
    'fixed',
    0.00,
    'CHF',
    '2 à 6 semaines'
),

(
    'SRV005',
    'Gouvernance et adoption IA',
    'Accompagnement dans la définition des règles de gouvernance et des bonnes pratiques d utilisation de l IA.',
    'Gouvernance',
    'fixed',
    0.00,
    'CHF',
    'Selon projet'
),

(
    'SRV006',
    'Accompagnement mensuel',
    'Support continu, amélioration des automatisations et accompagnement des équipes dans l adoption de l IA.',
    'Accompagnement',
    'subscription',
    0.00,
    'CHF',
    'Mensuel'
);