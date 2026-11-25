# ClairIA CRM — Proposition d'architecture (étape 1, à valider)

> Document de cadrage. Aucun code applicatif n'est produit avant validation. Aucun secret n'y figure.

## 1. Analyse des besoins

- **Site public** (5 pages) : génère des demandes → `website_requests`.
- **CRM sécurisé** (utilisateurs internes, Entra ID) : demandes, prospects, contacts, clients, opportunités, activités, services, devis (+lignes), factures (+lignes), dépenses.
- **Dashboard direction** : CA, pipeline total/pondéré, nouveaux prospects, conversion, panier moyen, prévisions, opportunités par étape, prospects par canton/origine, performance par service, impayés, dépenses inhabituelles. Basé en priorité sur `vw_sales_pipeline`, `vw_monthly_revenue`, `vw_prospect_statistics`.
- **Parcours** : visiteur → formulaire → `website_requests` → recherche d'entreprise existante → prospect (création/MAJ) → assignation → activité → qualification → opportunité → devis → client → facture. Chaque étape importante exige une **validation humaine** (« L'humain décide »).
- **Base** : `clairia_crm` (MySQL ≥ 8.0.16), 13 tables, 3 vues, déjà existante : le schéma est la source de vérité, l'application ne le recrée pas.
- **Données manquantes** : les DDL exacts (colonnes, enums, contraintes) ne sont pas fournis ; il faut les exporter (`mysqldump --no-data`) avant de coder.

## 2. Pile technologique (proposée)

| Couche | Choix | Justification |
|---|---|---|
| Langage | TypeScript (Node.js 20 LTS) | Un seul langage front/back, bien supporté par Copilot et App Service |
| Framework | **Next.js (App Router)** monolithe | Site public (SSR/SEO) + CRM + API dans une seule application, un seul déploiement |
| Accès MySQL | **Drizzle ORM + mysql2** (schéma introspecté via `drizzle-kit introspect`), SQL brut paramétré pour les vues | Ne recrée pas le modèle ; requêtes paramétrées ; typage |
| Validation | Zod (partagé client/serveur) | Validation côté serveur systématique |
| Auth | Auth.js (NextAuth) avec fournisseur Microsoft Entra ID (OIDC) | Standard, rôles via App Roles/groupes |
| UI | Tailwind CSS + composants accessibles (Radix/shadcn), graphiques Recharts | Sobre, accessible, responsive, charte ClairIA via tokens |
| Logs | pino (masquage des champs sensibles) + Application Insights | Journaux techniques sans données personnelles |
| Tests | Vitest (unitaire), Playwright (E2E), Testcontainers MySQL 8 (intégration) | Testable localement et en CI |
| CI/CD | GitHub Actions | Déploiement vers App Service |

Alternative possible : ASP.NET Core + EF Core (si compétences .NET préférées). À trancher (§12).

## 3. Architecture applicative

Monolithe modulaire en couches :

```
Navigateur ─► Next.js (App Service)
              ├─ (public)  pages + POST /api/public/requests (anonyme, rate-limité)
              ├─ (crm)     pages protégées + Server Actions / route handlers
              │     └─ middleware : session Entra + contrôle de rôle
              ├─ services/ (logique métier, transactions, règles de conversion)
              ├─ repositories/ (Drizzle, SQL paramétré)
              └─ lib/ (auth, env, logger, erreurs, validation)
                        │  (VNet / Private Endpoint)
                        ▼
              Azure Database for MySQL Flexible Server  `clairia_crm`
```

Principes : séparation stricte public/CRM (groupes de routes, middleware, schémas de validation distincts) ; la logique métier est dans `services/`, jamais dans les composants ; erreurs centralisées ; une couche `reporting/` isole les requêtes du dashboard (réutilisable par Power BI / Copilot Studio plus tard).

## 4. Arborescence du dépôt

```
/
├─ .github/
│  ├─ workflows/ (ci.yml, deploy.yml)
│  ├─ ISSUE_TEMPLATE/ , copilot-instructions.md
├─ docs/ (ARCHITECTURE.md, DATA_MODEL.md, SECURITY.md, DEPLOYMENT.md, adr/)
├─ db/ (schema-reference.sql, seed-dev.sql, migrations/ — évolutions additives uniquement)
├─ infra/ (bicep/ : App Service, Key Vault, MySQL, VNet, App Insights)
├─ src/
│  ├─ app/
│  │  ├─ (public)/ page.tsx, services/, a-propos/, contact/, diagnostic/
│  │  ├─ (crm)/crm/ dashboard/, demandes/, prospects/, contacts/, clients/,
│  │  │            opportunites/, activites/, services/, devis/, factures/, depenses/
│  │  └─ api/ auth/[...nextauth]/, public/requests/, health/, crm/**
│  ├─ components/ (ui/, public/, crm/, charts/)
│  ├─ modules/<domaine>/ (schema.ts, repository.ts, service.ts, actions.ts, *.test.ts)
│  ├─ db/ (client.ts, schema/ introspecté, views.ts)
│  ├─ lib/ (env.ts, auth.ts, rbac.ts, logger.ts, errors.ts, rate-limit.ts, money.ts)
│  └─ styles/ (tokens ClairIA)
├─ tests/ (integration/, e2e/)
├─ .env.example
└─ package.json, tsconfig.json, README.md
```

## 5. Modules, routes et responsabilités

| Module | Routes CRM | Responsabilité |
|---|---|---|
| website-requests | `/crm/demandes` | Liste, détail, statut, conversion en prospect (avec détection de doublon) |
| prospects | `/crm/prospects` | CRUD, assignation, statut, conversion en client (confirmation) |
| contacts | `/crm/contacts` | CRUD rattaché à prospect/client |
| clients | `/crm/clients` | Fiche 360° (contacts, opportunités, devis, factures) |
| opportunities | `/crm/opportunites` | Pipeline (vue kanban par étape), probabilité, montant |
| activities | `/crm/activites` | Planifier, clôturer, retards |
| services | `/crm/services` | Catalogue (admin/manager) |
| quotes | `/crm/devis` | Devis + lignes, statuts, conversion en facture |
| invoices | `/crm/factures` | Factures + lignes, paiements, impayés/échéances |
| expenses | `/crm/depenses` | Saisie, détection d'anomalies (seuil / écart à la moyenne par catégorie) |
| dashboard | `/crm/dashboard` | KPIs via les 3 vues + requêtes complémentaires |

Public : `/`, `/services`, `/a-propos`, `/contact`, `/diagnostic` ; API `POST /api/public/requests`.

**Règles clés** : anti-doublon (e-mail normalisé, nom d'entreprise normalisé, contrôle avant création) ; opérations multi-tables en transaction ; actions sensibles (conversion client, envoi/acceptation devis, émission facture, suppression) soumises à confirmation explicite et tracées dans `activities`.

**Rôles** : `admin` (tout, utilisateurs, catalogue), `manager` (lecture globale, dashboard, validation devis/factures/dépenses), `commercial` (ses prospects/opportunités/activités, création de devis). Contrôle dans `rbac.ts` et dans les services (jamais seulement l'UI).

## 6. Stratégie d'accès MySQL

- Connexion unique poolée (`mysql2/promise`), TLS obligatoire (Azure MySQL), compte applicatif dédié aux droits minimaux (SELECT/INSERT/UPDATE sur les tables nécessaires, pas de DDL, pas de DELETE sauf besoin validé).
- Aucune concaténation SQL : ORM ou `?` paramétrés. Pour les vues : requêtes préparées en lecture seule.
- Schéma existant introspecté et versionné ; les enums MySQL sont reflétés en Zod ; aucune migration destructive. Évolutions via scripts additifs revus.
- Montants : `DECIMAL` manipulé comme chaîne/entier de centimes (pas de flottants), devise CHF, formatage `fr-CH`.
- Réseau : Flexible Server en accès privé (VNet integration / Private Endpoint), pas d'accès public.
- Formulaire public : compte/permission restreints à `INSERT` sur `website_requests`.

## 7. Intégration Microsoft Entra ID

- Inscription d'application (single-tenant) ; flux OIDC code + PKCE via Auth.js.
- **App Roles** `admin`, `manager`, `commercial` assignés dans l'application d'entreprise (ou groupes de sécurité) ; rôles lus dans le jeton.
- Rapprochement avec `users` par e-mail/ID objet Entra (provisionnement à la première connexion, rôle jamais élevé automatiquement) ; utilisateur désactivé dans `users` = accès refusé.
- Middleware : toute route `/crm/**` et `/api/crm/**` exige session valide + rôle ; sessions courtes, cookies `HttpOnly`/`Secure`/`SameSite=Lax`.
- Plus tard : jetons dédiés pour Power BI (service principal, lecture seule) et Copilot Studio (connecteur personnalisé / API protégée par Entra).

## 8. Variables d'environnement (noms uniquement)

```
NODE_ENV, APP_BASE_URL, LOG_LEVEL
AUTH_SECRET, AUTH_TRUST_HOST
AZURE_AD_TENANT_ID, AZURE_AD_CLIENT_ID, AZURE_AD_CLIENT_SECRET
DB_HOST, DB_PORT, DB_NAME (=clairia_crm), DB_USER, DB_PASSWORD, DB_SSL_CA (optionnel), DB_POOL_SIZE
PUBLIC_FORM_RATE_LIMIT_PER_HOUR, UNUSUAL_EXPENSE_THRESHOLD_CHF (ou facteur)
APPLICATIONINSIGHTS_CONNECTION_STRING
```
`.env.example` sans valeurs ; `.env*` ignoré par Git ; validation au démarrage via Zod (échec explicite si manquant). En Azure : **Key Vault** + références Key Vault dans les App Settings, identité managée de l'App Service. Option ultérieure : authentification MySQL par Entra/identité managée.

## 9. Étapes de développement

1. Fondations : dépôt, TypeScript, lint, CI, `env.ts`, logger, erreurs.
2. Introspection du schéma, DATA_MODEL.md, jeu de données de dev, conteneur MySQL local.
3. Authentification Entra + rôles + layout CRM.
4. Site public + charte + formulaire + enregistrement `website_requests` (rate-limit, honeypot).
5. Demandes → prospects (anti-doublon) → assignation → activités.
6. Contacts, clients, conversion prospect → client.
7. Opportunités et pipeline.
8. Catalogue services, devis et lignes.
9. Factures et lignes, impayés.
10. Dépenses et détection d'anomalies.
11. Dashboard (3 vues + requêtes complémentaires).
12. Durcissement sécurité, accessibilité (WCAG 2.1 AA), E2E.
13. Infra Bicep, déploiement Azure, observabilité.
14. Préparation Power BI / Copilot Studio (API de lecture, documentation).

## 10. Premiers tests automatisés

- Unitaires : schémas Zod du formulaire public (champs requis, e-mail, longueurs, date future) ; normalisation e-mail/entreprise ; calcul de pipeline pondéré, taux de conversion, panier moyen ; arrondis CHF ; règles RBAC ; détection d'anomalie de dépense.
- Intégration (MySQL 8 éphémère) : insertion `website_requests` ; conversion demande → prospect sans doublon ; prospect → client en transaction ; contraintes FK/enums respectées ; lecture des 3 vues ; tentative d'injection SQL neutralisée.
- API/sécurité : `/crm/**` sans session → 401/redirection ; rôle insuffisant → 403 ; rate-limit formulaire ; erreurs sans fuite de détails ; logs sans e-mail/secret.
- E2E (Playwright) : parcours formulaire public ; connexion simulée et parcours demande → prospect → devis ; contrôles d'accessibilité (axe).

## 11. Déploiement Azure App Service

- Ressources (Bicep) : Resource Group, App Service Plan Linux (B1/P1v3), Web App Node 20, Azure Database for MySQL Flexible Server (privé), VNet + intégration, Key Vault, Application Insights, slot `staging`.
- GitHub Actions : lint → tests → build → déploiement du slot staging (OIDC vers Azure, sans secret stocké) → smoke test `/api/health` → swap vers production.
- Environnements : local (Docker MySQL), staging, production, avec bases séparées ; sauvegardes MySQL et rétention ; HTTPS only, TLS ≥ 1.2, domaine personnalisé.

## 12. Risques et décisions à valider

| # | Point | Recommandation |
|---|---|---|
| 1 | Pile TypeScript/Next.js vs .NET | Next.js proposé ; à confirmer |
| 2 | DDL exact des tables/enums/vues non fourni | Fournir `mysqldump --no-data` avant le développement |
| 3 | Rôles Entra : App Roles vs groupes ; locataire disponible ? | App Roles |
| 4 | Lien `users` ↔ identité Entra (colonne à ajouter ?) | Vérifier le schéma ; ajout additif seulement si nécessaire |
| 5 | Règle de doublon (nom, e-mail, IDE/UID, domaine ?) | E-mail + nom d'entreprise normalisé |
| 6 | Seuil « dépense inhabituelle » | Écart > 2 σ ou seuil par catégorie, paramétrable |
| 7 | TVA suisse (8,1 %), numérotation et QR-facture | Hors V1 sauf demande ; vérifier colonnes existantes |
| 8 | RGPD / nLPD : consentement, conservation, suppression des demandes | Mention de consentement + politique de rétention |
| 9 | Spam du formulaire public | Honeypot + rate-limit ; CAPTCHA éventuel |
| 10 | Données personnelles dans les logs | Masquage systématique |
| 11 | Langue : fr-CH uniquement en V1 | i18n différée |
| 12 | Coûts Azure (MySQL privé, plan) | Estimer avant provisionnement |

## 13. Premières tâches GitHub à créer

1. Initialiser le dépôt (Next.js/TS, lint, format, Vitest, structure de dossiers).
2. CI GitHub Actions (lint, tests, build).
3. Exporter et documenter le schéma `clairia_crm` (DATA_MODEL.md, `db/schema-reference.sql`).
4. Environnement local Docker MySQL + seed de dev.
5. Module `env.ts` (validation Zod) + `.env.example` + logger + gestion d'erreurs centralisée.
6. Introspection Drizzle et couche d'accès MySQL (pool, TLS).
7. Authentification Entra ID (Auth.js) + RBAC + middleware.
8. Charte ClairIA (tokens, typographie Aptos/sans-serif, layout public et CRM).
9. Pages publiques + formulaire de diagnostic + `POST /api/public/requests`.
10. Module demandes Web → prospects avec anti-doublon.
11. Infra Bicep (App Service, Key Vault, MySQL, App Insights) et workflow de déploiement.
12. Rédiger SECURITY.md et les ADR des décisions du §12.
