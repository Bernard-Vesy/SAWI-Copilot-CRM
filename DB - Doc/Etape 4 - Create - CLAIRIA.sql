-- ============================================================
-- CLAIRIA CRM
-- Base de données MySQL
-- Version : 1.0
-- Projet : Masterclass Microsoft Copilot
-- ============================================================

-- CREATE DATABASE IF NOT EXISTS clairia_crm
-- CHARACTER SET utf8mb4
-- COLLATE utf8mb4_unicode_ci;

-- USE clairia_crm;

-- ============================================================
-- TABLE 1 : USERS
-- Gestion des utilisateurs du CRM
-- ============================================================

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    role ENUM('admin', 'commercial', 'manager')
        NOT NULL DEFAULT 'commercial',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 2 : PROSPECTS
-- Gestion des entreprises prospectées
-- ============================================================

CREATE TABLE prospects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(30),
    website VARCHAR(255),
    industry VARCHAR(100),
    company_size INT,
    address VARCHAR(255),
    postal_code VARCHAR(20),
    city VARCHAR(100),
    canton VARCHAR(50),
    country VARCHAR(100) DEFAULT 'Suisse',
    source VARCHAR(100),
    status ENUM(
        'new',
        'contacted',
        'qualified',
        'converted',
        'lost'
    ) NOT NULL DEFAULT 'new',
    potential_value DECIMAL(12,2) DEFAULT 0,
    conversion_probability DECIMAL(5,2) DEFAULT 0,
    assigned_user_id INT,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_prospects_user
        FOREIGN KEY (assigned_user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,

    CONSTRAINT chk_prospect_probability
        CHECK (conversion_probability BETWEEN 0 AND 100),

    CONSTRAINT chk_prospect_value
        CHECK (potential_value >= 0),

    CONSTRAINT chk_prospect_company_size
        CHECK (company_size IS NULL OR company_size >= 0),

    INDEX idx_prospects_status (status),
    INDEX idx_prospects_canton (canton),
    INDEX idx_prospects_source (source),
    INDEX idx_prospects_industry (industry),
    INDEX idx_prospects_created (created_at)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 3 : CLIENTS
-- Gestion du portefeuille clients
-- ============================================================

CREATE TABLE clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prospect_id INT UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    company_size INT,
    email VARCHAR(255),
    phone VARCHAR(30),
    address VARCHAR(255),
    postal_code VARCHAR(20),
    city VARCHAR(100),
    canton VARCHAR(50),
    country VARCHAR(100) DEFAULT 'Suisse',
    vat_number VARCHAR(50),
    status ENUM(
        'active',
        'inactive',
        'lost'
    ) NOT NULL DEFAULT 'active',
    assigned_user_id INT,
    customer_since DATE,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_clients_prospect
        FOREIGN KEY (prospect_id)
        REFERENCES prospects(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_clients_user
        FOREIGN KEY (assigned_user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,

    CONSTRAINT chk_client_company_size
        CHECK (company_size IS NULL OR company_size >= 0),

    INDEX idx_clients_status (status),
    INDEX idx_clients_canton (canton),
    INDEX idx_clients_industry (industry)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 4 : CONTACTS
-- Personnes associées aux prospects et clients
-- ============================================================

CREATE TABLE contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prospect_id INT,
    client_id INT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    job_title VARCHAR(150),
    email VARCHAR(255),
    phone VARCHAR(30),
    mobile VARCHAR(30),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_contacts_prospect
        FOREIGN KEY (prospect_id)
        REFERENCES prospects(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_contacts_client
        FOREIGN KEY (client_id)
        REFERENCES clients(id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_contact_owner
        CHECK (
            (prospect_id IS NOT NULL AND client_id IS NULL)
            OR
            (prospect_id IS NULL AND client_id IS NOT NULL)
        ),

    INDEX idx_contacts_email (email),
    INDEX idx_contacts_prospect (prospect_id),
    INDEX idx_contacts_client (client_id)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 5 : SERVICES
-- Catalogue des prestations ClairIA
-- ============================================================

CREATE TABLE services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    pricing_model ENUM(
        'fixed',
        'hourly',
        'daily',
        'subscription'
    ) NOT NULL DEFAULT 'fixed',
    unit_price DECIMAL(12,2) NOT NULL DEFAULT 0,
    currency CHAR(3) NOT NULL DEFAULT 'CHF',
    estimated_duration VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_service_price
        CHECK (unit_price >= 0),

    INDEX idx_services_category (category)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 6 : OPPORTUNITIES
-- Pipeline commercial
-- ============================================================

CREATE TABLE opportunities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prospect_id INT,
    client_id INT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    service_id INT,
    estimated_value DECIMAL(12,2) NOT NULL DEFAULT 0,
    probability DECIMAL(5,2) NOT NULL DEFAULT 0,
    stage ENUM(
        'qualification',
        'discovery',
        'proposal',
        'negotiation',
        'won',
        'lost'
    ) NOT NULL DEFAULT 'qualification',
    expected_close_date DATE,
    actual_close_date DATE,
    assigned_user_id INT,
    loss_reason TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_opportunities_prospect
        FOREIGN KEY (prospect_id)
        REFERENCES prospects(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_opportunities_client
        FOREIGN KEY (client_id)
        REFERENCES clients(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_opportunities_service
        FOREIGN KEY (service_id)
        REFERENCES services(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_opportunities_user
        FOREIGN KEY (assigned_user_id)
        REFERENCES users(id)
        ON DELETE SET NULL,

    CONSTRAINT chk_opportunity_owner
        CHECK (
            (prospect_id IS NOT NULL AND client_id IS NULL)
            OR
            (prospect_id IS NULL AND client_id IS NOT NULL)
        ),

    CONSTRAINT chk_opportunity_probability
        CHECK (probability BETWEEN 0 AND 100),

    CONSTRAINT chk_opportunity_value
        CHECK (estimated_value >= 0),

    INDEX idx_opportunities_stage (stage),
    INDEX idx_opportunities_close (expected_close_date),
    INDEX idx_opportunities_service (service_id)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 7 : ACTIVITIES
-- Historique des interactions commerciales
-- ============================================================

CREATE TABLE activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prospect_id INT,
    client_id INT,
    opportunity_id INT,
    contact_id INT,
    user_id INT NOT NULL,
    activity_type ENUM(
        'call',
        'email',
        'meeting',
        'task',
        'demo',
        'other'
    ) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM(
        'planned',
        'completed',
        'cancelled'
    ) NOT NULL DEFAULT 'planned',
    due_date DATETIME,
    completed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_activities_prospect
        FOREIGN KEY (prospect_id)
        REFERENCES prospects(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_activities_client
        FOREIGN KEY (client_id)
        REFERENCES clients(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_activities_opportunity
        FOREIGN KEY (opportunity_id)
        REFERENCES opportunities(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_activities_contact
        FOREIGN KEY (contact_id)
        REFERENCES contacts(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_activities_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_activity_owner
        CHECK (
            prospect_id IS NOT NULL
            OR client_id IS NOT NULL
            OR opportunity_id IS NOT NULL
            OR contact_id IS NOT NULL
        ),

    INDEX idx_activities_type (activity_type),
    INDEX idx_activities_status (status),
    INDEX idx_activities_due (due_date)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 8 : QUOTES
-- Gestion des devis
-- ============================================================

CREATE TABLE quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quote_number VARCHAR(50) NOT NULL UNIQUE,
    prospect_id INT,
    client_id INT,
    opportunity_id INT,
    issue_date DATE NOT NULL,
    valid_until DATE,
    status ENUM(
        'draft',
        'sent',
        'accepted',
        'rejected',
        'expired'
    ) NOT NULL DEFAULT 'draft',
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0,
    tax_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    tax_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    currency CHAR(3) NOT NULL DEFAULT 'CHF',
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_quotes_prospect
        FOREIGN KEY (prospect_id)
        REFERENCES prospects(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_quotes_client
        FOREIGN KEY (client_id)
        REFERENCES clients(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_quotes_opportunity
        FOREIGN KEY (opportunity_id)
        REFERENCES opportunities(id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_quote_owner
        CHECK (
            (prospect_id IS NOT NULL AND client_id IS NULL)
            OR
            (prospect_id IS NULL AND client_id IS NOT NULL)
        ),

    CONSTRAINT chk_quote_amounts
        CHECK (
            subtotal >= 0
            AND tax_rate BETWEEN 0 AND 100
            AND tax_amount >= 0
            AND total_amount >= 0
        ),

    CONSTRAINT chk_quote_dates
        CHECK (valid_until IS NULL OR valid_until >= issue_date),

    INDEX idx_quotes_status (status),
    INDEX idx_quotes_issue_date (issue_date)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 9 : QUOTE_ITEMS
-- Lignes des devis
-- ============================================================

CREATE TABLE quote_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quote_id INT NOT NULL,
    service_id INT,
    description VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 1,
    unit_price DECIMAL(12,2) NOT NULL DEFAULT 0,
    tax_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    line_total DECIMAL(12,2) NOT NULL DEFAULT 0,
    sort_order INT NOT NULL DEFAULT 0,

    CONSTRAINT fk_quote_items_quote
        FOREIGN KEY (quote_id)
        REFERENCES quotes(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_quote_items_service
        FOREIGN KEY (service_id)
        REFERENCES services(id)
        ON DELETE SET NULL,

    CONSTRAINT chk_quote_item_values
        CHECK (
            quantity > 0
            AND unit_price >= 0
            AND tax_rate BETWEEN 0 AND 100
            AND line_total >= 0
        ),

    INDEX idx_quote_items_quote (quote_id)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 10 : INVOICES
-- Gestion de la facturation
-- ============================================================

CREATE TABLE invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    client_id INT NOT NULL,
    quote_id INT,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    payment_date DATE,
    status ENUM(
        'draft',
        'sent',
        'partially_paid',
        'paid',
        'overdue',
        'cancelled'
    ) NOT NULL DEFAULT 'draft',
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0,
    tax_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    amount_paid DECIMAL(12,2) NOT NULL DEFAULT 0,
    currency CHAR(3) NOT NULL DEFAULT 'CHF',
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_invoices_client
        FOREIGN KEY (client_id)
        REFERENCES clients(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_invoices_quote
        FOREIGN KEY (quote_id)
        REFERENCES quotes(id)
        ON DELETE RESTRICT,

    CONSTRAINT chk_invoice_dates
        CHECK (due_date >= issue_date),

    CONSTRAINT chk_invoice_amounts
        CHECK (
            subtotal >= 0
            AND tax_amount >= 0
            AND total_amount >= 0
            AND amount_paid >= 0
            AND amount_paid <= total_amount
        ),

    INDEX idx_invoices_status (status),
    INDEX idx_invoices_issue_date (issue_date),
    INDEX idx_invoices_due_date (due_date)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 11 : INVOICE_ITEMS
-- Lignes des factures
-- ============================================================

CREATE TABLE invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    service_id INT,
    description VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 1,
    unit_price DECIMAL(12,2) NOT NULL DEFAULT 0,
    tax_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    line_total DECIMAL(12,2) NOT NULL DEFAULT 0,
    sort_order INT NOT NULL DEFAULT 0,

    CONSTRAINT fk_invoice_items_invoice
        FOREIGN KEY (invoice_id)
        REFERENCES invoices(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_invoice_items_service
        FOREIGN KEY (service_id)
        REFERENCES services(id)
        ON DELETE SET NULL,

    CONSTRAINT chk_invoice_item_values
        CHECK (
            quantity > 0
            AND unit_price >= 0
            AND tax_rate BETWEEN 0 AND 100
            AND line_total >= 0
        ),

    INDEX idx_invoice_items_invoice (invoice_id)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 12 : EXPENSES
-- Suivi des charges
-- ============================================================

CREATE TABLE expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    expense_date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    supplier VARCHAR(255),
    description TEXT,
    amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    tax_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    currency CHAR(3) NOT NULL DEFAULT 'CHF',
    payment_status ENUM(
        'pending',
        'paid'
    ) NOT NULL DEFAULT 'pending',
    payment_date DATE,
    created_by INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_expenses_user
        FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,

    CONSTRAINT chk_expense_amounts
        CHECK (
            amount >= 0
            AND tax_amount >= 0
            AND total_amount >= 0
        ),

    INDEX idx_expenses_date (expense_date),
    INDEX idx_expenses_category (category),
    INDEX idx_expenses_status (payment_status)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 13 : WEBSITE_REQUESTS
-- Formulaires provenant du site Web ClairIA
-- ============================================================

CREATE TABLE website_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(30),
    request_type ENUM(
        'contact',
        'diagnostic',
        'appointment'
    ) NOT NULL DEFAULT 'contact',
    message TEXT,
    preferred_date DATETIME,
    status ENUM(
        'new',
        'processed',
        'closed'
    ) NOT NULL DEFAULT 'new',
    prospect_id INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_website_requests_prospect
        FOREIGN KEY (prospect_id)
        REFERENCES prospects(id)
        ON DELETE RESTRICT,

    INDEX idx_website_requests_status (status),
    INDEX idx_website_requests_created (created_at),
    INDEX idx_website_requests_email (email)
) ENGINE=InnoDB;