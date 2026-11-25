# SAWI-Copilot-CRM
Application Web FastAPI pour ClairIA, société de services informatiques et IA. Elle permet de centraliser prospects, clients, contacts, opportunités, activités commerciales, services, devis et factures, et d’offrir une vue simple et structurée du pipeline commercial et de l’activité de l’entreprise.

# ClairIA CRM

> **L’IA concrète pour les PME.**  
> *L’humain décide. L’IA accélère.*

## Présentation

ClairIA est une entreprise fictive créée dans le cadre de la **Masterclass Microsoft Copilot**. Elle accompagne les PME de Suisse romande dans l’adoption concrète, progressive et sécurisée de l’intelligence artificielle, de Microsoft Copilot et de l’automatisation.

Ce dépôt a pour objectif de construire une application Web moderne regroupant :

- un **site Internet public** présentant ClairIA et ses services ;
- un **CRM sécurisé** pour suivre prospects, contacts, clients et opportunités ;
- la gestion des activités commerciales, devis, factures et dépenses ;
- un **dashboard commercial et financier** ;
- une base technique permettant de futures connexions avec **Power BI** et **Microsoft Copilot Studio**.

## Objectif pédagogique

Le projet fait partie du fil rouge de la Masterclass : partir de zéro et utiliser l’écosystème Copilot pour imaginer, créer, exploiter et piloter une petite entreprise de services IA.

Le parcours global suit la logique :

**Imaginer → Créer → Concevoir → Développer → Vendre → Analyser → Explorer → Automatiser → Piloter**

L’application constitue la phase de développement : **GitHub Copilot + Azure + MySQL**.

## Positionnement de ClairIA

ClairIA vise les PME de services de Suisse romande qui souhaitent obtenir des résultats concrets avec l’IA sans lancer un projet informatique disproportionné.

L’approche privilégie :

- les besoins métier avant la technologie ;
- les cas d’usage réels ;
- l’adoption progressive ;
- la formation pratique des collaborateurs ;
- la sécurité et la gouvernance ;
- des résultats observables et mesurables.

## Services

Le catalogue ClairIA comprend six prestations :

1. **Diagnostic découverte IA**
2. **Audit Copilot et feuille de route**
3. **Formation Microsoft Copilot**
4. **Prototype et automatisation**
5. **Gouvernance et adoption IA**
6. **Accompagnement mensuel**

## Application Web

L’application est organisée en deux espaces principaux.

### Site public

Pages prévues :

- Accueil
- Services
- À propos
- Contact
- Demande de rendez-vous / diagnostic IA

Le formulaire public permet notamment de recueillir les demandes commerciales et de les enregistrer dans `website_requests`.

### CRM sécurisé

Le CRM doit permettre de gérer :

- demandes Web ;
- prospects ;
- contacts ;
- clients ;
- opportunités ;
- activités commerciales ;
- services ;
- devis ;
- factures ;
- dépenses.

### Parcours commercial

```text
Visiteur
   ↓
Formulaire Web
   ↓
website_requests
   ↓
Vérification de l’entreprise
   ↓
Création / mise à jour du prospect
   ↓
Attribution à un commercial
   ↓
Activité commerciale
   ↓
Qualification
   ↓
Opportunité
   ↓
Devis
   ↓
Client
   ↓
Facturation
   ↓
Analyse
```

## Base de données

La base existante est :

```text
clairia_crm
```

Compatibilité prévue : **MySQL 8.0.16+**.

### Tables

La version actuelle comprend 13 tables :

```text
users
prospects
contacts
clients
opportunities
activities
services
quotes
quote_items
invoices
invoice_items
expenses
website_requests
```

Le modèle utilise notamment des clés étrangères, contraintes de validation et index afin de préserver la cohérence des données et de faciliter les recherches courantes.

### Vues SQL

Trois vues SQL facultatives sont décrites pour l’analyse :

```text
vw_sales_pipeline
vw_monthly_revenue
vw_prospect_statistics
```

- `vw_sales_pipeline` : suivi des opportunités et de leur valeur pondérée ;
- `vw_monthly_revenue` : analyse mensuelle du chiffre d’affaires facturé ;
- `vw_prospect_statistics` : analyse des prospects par canton, secteur, origine et statut.

L’application calcule ses indicateurs à partir des tables existantes et ne dépend pas de ces vues.

## Dashboard

Les principaux indicateurs prévus sont :

- chiffre d’affaires ;
- pipeline commercial ;
- nouveaux prospects ;
- taux de conversion ;
- panier moyen ;
- prévisions commerciales.

Les visualisations envisagées comprennent notamment :

- évolution mensuelle du chiffre d’affaires ;
- opportunités par étape ;
- prospects par canton ;
- prospects par origine ;
- pipeline pondéré par commercial ;
- performance commerciale par service.

## Identité visuelle

### Couleurs

| Usage | Couleur | Code |
|---|---|---|
| Institutionnel | Bleu nuit | `#14243A` |
| IA / innovation | Bleu électrique | `#3979F6` |
| Humain | Turquoise | `#22B8A7` |
| Accent | Corail | `#FF7A66` |
| Fond clair | Gris brume | `#F3F6F8` |
| Texte | Anthracite | `#222831` |
| Blanc | Blanc pur | `#FFFFFF` |

Le corail est utilisé avec parcimonie comme couleur d’accent.

### Ton

L’interface et les contenus doivent rester :

- clairs ;
- rassurants ;
- pragmatiques ;
- humains ;
- orientés résultats.

Les visuels futuristes, robots humanoïdes, cerveaux électroniques et codes graphiques de science-fiction sont à éviter.

## Sécurité

Les principes retenus pour le projet comprennent :

- authentification sécurisée ;
- utilisation recommandée de **Microsoft Entra ID** pour les utilisateurs internes ;
- accès MySQL limités aux services applicatifs autorisés ;
- aucun identifiant de connexion stocké directement dans le code source ;
- contrôle de la cohérence des données dans la base et dans les règles métier applicatives ;
- sauvegardes régulières et procédure de restauration à prévoir.

Les rôles actuellement définis dans la table `users` sont :

```text
admin
commercial
manager
```

## Déploiement cible

L’application est destinée à pouvoir être hébergée sur **Microsoft Azure App Service**.

L’architecture doit rester suffisamment simple pour être développée, maintenue et déployée dans le cadre pédagogique de la Masterclass, tout en préparant de futures intégrations avec :

- Power BI ;
- Microsoft Copilot Studio.

## Évolutions possibles

Le modèle actuel est volontairement limité. Les évolutions envisagées comprennent :

- `payments` pour les paiements multiples et acomptes ;
- `budgets` pour comparer budget et réel ;
- `audit_logs` pour l’historique des modifications sensibles ;
- `attachments` pour rattacher des documents aux objets métiers, avec possibilité de stocker les fichiers dans Azure Blob Storage et les références dans MySQL.

## Données de démonstration

Un jeu de données entièrement fictif est prévu pour les démonstrations. Il doit permettre d’illustrer des cas tels que :

- prospects récents ou sans activité ;
- opportunités gagnées, perdues ou stagnantes ;
- différents niveaux de probabilité ;
- devis acceptés ou refusés ;
- factures payées, partiellement payées ou impayées ;
- dépenses inhabituelles ;
- revenus récurrents.

Les données personnelles de démonstration ne doivent correspondre à aucune personne réelle.

## Principes de développement

Pour la première version :

1. analyser et respecter le modèle MySQL existant ;
2. privilégier une architecture simple et maintenable ;
3. séparer clairement le site public et l’espace CRM sécurisé ;
4. préserver les contraintes et relations de la base ;
5. ne jamais stocker de secrets dans le dépôt ;
6. préparer la solution pour Azure, Power BI et Copilot Studio ;
7. conserver une logique pédagogique compréhensible pendant toute la Masterclass.

## Contexte du projet

Ce dépôt est un projet de démonstration pédagogique de la **Masterclass Microsoft Copilot**.

Il illustre le passage de la conception avec Copilot à la construction avec GitHub Copilot, puis à l’exploitation des mêmes données dans Power BI, Excel et des scénarios d’automatisation par agents.

---

**ClairIA**  
*L’IA concrète pour les PME.*

---

## Application FastAPI — développement local

L’application comprend le site public (Accueil, Services, À propos, Contact), la capture des demandes Web et un espace CRM protégé par rôle. Les enregistrements CRM peuvent être créés et modifiés; les suppressions sont désactivées afin de préserver l’historique et les relations existantes.

### Démarrer sans base de données

Prérequis : Python 3.13.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
python -m src.main
```

Dans VS Code, sélectionner l’interpréteur `.venv` et la configuration
**Python : lancer ClairIA**, puis appuyer sur **F5**. Le site est accessible à
`http://localhost:8000` par défaut.

Le site et `/healthz` fonctionnent sans connexion MySQL. Avec `DATABASE_ENABLED=false`, le formulaire de contact explique clairement que la demande n’est pas enregistrée; le CRM signale l’absence de base. Aucune base locale de démonstration ni aucun utilisateur ou mot de passe fictif n’est créé.

### Base MySQL dédiée aux tests

Ne pas activer la connexion avant d’avoir reçu et validé les contraintes réseau et TLS de la base dédiée aux tests. Ne jamais utiliser la base de production. `.env.example` ne contient que des valeurs d’exemple et des marqueurs de remplacement. Ne pas partager ni committer un fichier `.env`.

Une fois les paramètres approuvés, renseigner dans `.env` les valeurs `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_TLS_MODE` et `DB_TLS_CA`, puis basculer explicitement `DATABASE_ENABLED=true`. Les modes TLS acceptés sont `verify_identity` (recommandé), `verify_ca` et `disabled` pour le développement/test uniquement; TLS est obligatoire en production. Si un paramètre requis manque, `/readyz` renvoie `503` lorsque la base est activée. Une vérification `SELECT 1` est tentée uniquement quand la configuration est complète et explicitement activée; les pages/formulaires expliquent l’indisponibilité sans exposer de secret.

Le code utilise des requêtes paramétrées. Il ne contient aucun `create_all`, DDL, migration ou chargement de données. Le fichier `src/schema.py` décrit les 13 tables et les contraintes communiquées; il ne génère ni ne modifie de schéma.

### Authentification et rôles

- En local, le formulaire de connexion vérifie un utilisateur actif et un hash bcrypt dans la base de test configurée; aucun compte de test n’est fourni.
- En production, renseigner `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_REDIRECT_URI` et `SESSION_SECRET` dans la configuration sécurisée de l’hôte. L’identité Entra est associée à un utilisateur CRM actif par adresse e-mail.
- Les cookies sont HTTP-only, `SameSite=Lax` et sécurisés en production. Les formulaires qui modifient l’état sont protégés par jeton CSRF.
- Les rôles `admin`, `manager` et `commercial` sont contrôlés côté serveur. Les commerciaux ne voient et ne modifient que les enregistrements qui leur sont attribués, ainsi que les contacts/devis liés à leurs comptes. Les demandes Web sont réservées à l’admin et au manager. La gestion des services, factures et dépenses est réservée à l’admin et au manager; les suppressions sont désactivées.

### Tests hors ligne

```powershell
python -m pytest
```

Exécuter cette commande à la racine du projet. Dans VS Code, utiliser l’onglet
**Tests** pour lancer ou déboguer les tests.
Ne pas lancer directement un fichier `tests/test_*.py` comme script Python :
pytest est nécessaire pour découvrir et exécuter les tests.

Les tests utilisent uniquement des valeurs synthétiques et remplacent les accès MySQL par des faux. Ils vérifient la validation des formulaires, les rôles, les calculs des lignes de devis/factures et que l’accès MySQL est bloqué si la configuration n’est pas complète. Ils ne contactent aucun serveur de base de données. Aucun test d’intégration distant n’est activé par défaut.

### Azure App Service Linux

Configurer Python 3.13, les variables d’environnement et les secrets dans la configuration App Service (pas dans le dépôt). La cible Linux et le runtime Python sont documentés par [Microsoft Learn](https://learn.microsoft.com/azure/app-service/configure-language-python). Commande de démarrage :

```text
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT src.main:app
```

`PORT` est fourni par l’hôte (8000 en local). Les contrôles de santé sont `/healthz` (liveness sans dépendance DB) et `/readyz` (vérifie la configuration; exécute `SELECT 1` uniquement si la connexion DB est activée et complète). Aucun fichier d’infrastructure ni ressource Azure n’est généré par ce projet.

### Tables et contraintes

Le mapping de `src/schema.py` documente intégralement les tables fournies : `users`, `prospects`, `clients`, `contacts`, `services`, `opportunities`, `activities`, `quotes`, `quote_items`, `invoices`, `invoice_items`, `expenses` et `website_requests`. Il conserve les colonnes, enums, uniques, checks, index, références et suppressions en cascade/restriction/SET NULL spécifiées. Les rapports équivalents aux trois vues facultatives sont calculés depuis les tables; aucun DDL n’est nécessaire.

