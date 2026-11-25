# SAWI-Copilot-CRM
Application Power Apps CRM pour ClairIA, société de services informatiques et IA. Elle permet de centraliser prospects, clients, contacts, opportunités, activités commerciales, services, devis et factures, et d’offrir une vue simple et structurée du pipeline commercial et de l’activité de l’entreprise.

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

Trois vues sont prévues pour l’analyse :

```text
vw_sales_pipeline
vw_monthly_revenue
vw_prospect_statistics
```

- `vw_sales_pipeline` : suivi des opportunités et de leur valeur pondérée ;
- `vw_monthly_revenue` : analyse mensuelle du chiffre d’affaires facturé ;
- `vw_prospect_statistics` : analyse des prospects par canton, secteur, origine et statut.

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

