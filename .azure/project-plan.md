# ClairIA CRM — Project Plan

**Status:** Approved by the user on 2026-11-25  
**Purpose:** Build the local-first CRM application described in `README.md`; prepare it for a later deployment to Azure App Service.

## Application

- Python 3.13, FastAPI, server-rendered HTML templates, and static assets.
- One web application for the public site and the secured CRM.
- Azure target: App Service on Linux. No Azure resources are to be provisioned or deployed as part of this implementation.
- Public pages: Accueil, Services, À propos, Contact, and appointment/AI-diagnostic request form.
- CRM: website requests, prospects, contacts, clients, opportunities, activities, services, quotes, invoices, and expenses.
- Dashboards: revenue, pipeline and weighted forecast, prospects, conversion, average deal size, stage, canton, source, owner, and service metrics.
- Use the README's ClairIA colors, French copy, and human, pragmatic visual direction.

## Existing database and safety

- Existing MySQL 8.0.16+ database with the 13 tables named in the README and supplied DDL: `users`, `prospects`, `clients`, `contacts`, `services`, `opportunities`, `activities`, `quotes`, `quote_items`, `invoices`, `invoice_items`, `expenses`, and `website_requests`.
- Preserve table names, columns, foreign keys, checks, enums, and indexes. Map application data access to the existing schema.
- Do not create, migrate, alter, seed, or otherwise mutate the schema automatically. Do not execute DDL.
- Calculate dashboard reports from the tables; do not require the three optional SQL views.
- A remote, dedicated test database exists. Do not connect until its network and TLS constraints have been provided and reviewed. Never connect to production during development or tests.
- Use synthetic/fictitious data only in tests. No production data in fixtures.
- Database details and passwords are configuration-only; do not put real credentials in this plan or repository.

## Authentication and authorization

- Local development: local login for test accounts, using only a non-production test database/configuration.
- Production: Microsoft Entra ID; map the authenticated identity to an active CRM user.
- Enforce route and data authorization for roles `admin`, `commercial`, and `manager`.
- Validate access against assigned users where supported by the existing schema. Keep manager/admin reporting access distinct from commercial access.
- Use secure, HTTP-only production cookies, CSRF protection for state-changing forms, and parameterized SQL.

## Local configuration and tests

- Document Python 3.13 setup, local run, and test commands.
- Provide `.env.example` with placeholders for app mode, port, DB host/port/name/user/password, TLS settings, session signing key, and Entra settings. Keep `.env` ignored and never populate it with the password shared in chat.
- The app must start without a production database. Keep tests offline by default; integration tests may target only the dedicated remote test database after network/TLS configuration is supplied.
- Add focused tests for role authorization, workflow and validation rules, public request handling, dashboards, and database access safety.
- Do not create test fixtures containing real personal data.

## Acceptance criteria

1. Local application starts under Python 3.13 and serves `/healthz` plus a database-independent `/readyz`.
2. Public pages and request form work without CRM authentication.
3. CRM routes require authentication and enforce the three defined roles.
4. Data-access code matches the supplied MySQL tables without automatic schema changes.
5. Local tests use synthetic data and do not connect to production.
6. Azure App Service Linux startup and environment-based configuration are documented.
7. No real credentials are written to source files or committed configuration.

## Out of scope

- Azure infrastructure generation, provisioning, or deployment.
- Schema changes, migrations, production database access, email delivery, Power BI, or Copilot Studio integrations.
- Any workflow or schema extension not supported by the README and supplied DDL without additional user approval.
