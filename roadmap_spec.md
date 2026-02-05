# PROJET : LINKEDIN MARKET VALIDATION BOT - ROADMAP TECHNIQUE

## Contexte
L'objectif est de transformer le MVP actuel en un outil robuste de "Market Validation" capable de gérer des campagnes de prospection complexes pour des clients exigeants (ex: VP Engineering, CTO). Le système doit être capable de gérer des séquences de messages conditionnelles, du tagging de prospects, et un reporting précis, le tout avec une dépendance minimale aux services tiers coûteux (Apify) pour la messagerie.

## Phase 1 : Consolidation & Segmentation (Fondations) - ✅ COMPLET
**Objectif :** Préparer la base de données pour gérer des segments et des tags précis (A/B/C, Hors Cible).

### 1.1 Amélioration du Modèle de Données (`models.py`)
- [x] Ajouter une table `Tags` (id, name, color).
- [x] Ajouter une table d'association `ProspectTags`.
- [x] Ajouter les champs de ciblage dans `Prospect` : `company_size`.

### 1.2 Stratégie de Sourcing (Adaptation Système Actuel)
**Approche :** Utiliser ton moteur de recherche actuel (SearchAPI) pour remplacer Sales Navigator.
- [x] **Recherche Ciblée** : Dashboard UX améliorée avec constructeur de requêtes Google (`site:linkedin.com/in/ "Role" "Industry"`).
- [x] **Logique d'Auto-Segmentation (Backend)** :
    - **Sources de données** : Le script lit `company_size` (colonne) ou fallback sur le JSON `experiences` si vide (ex: legacy data).
    - **Parsing Robuste** : Gère les formats complexes (ex: "10,001+" -> 10001).
    - **Règles d'Assignation** :
        - 11-100 employés -> **Segment A (11-100)**
        - 101-500 employés -> **Segment B (101-500)**
        - 501-2000 employés -> **Segment C (501-2000)** (Mappé aussi pour 2001-5000 pour la sûreté)
        - 1-10 ou >5000 -> **Hors Cible**
- [x] **Mise à jour UI** : Filtres responsives par Tags dans la vue Prospects.

### 1.3 Extensions "Signal Tags" & Géographie (Phase 1.5 - En cours)
- [ ] **Signal Tags** : Analyse sémantique (Headline/About) pour détecter :
    - `Platform/DevEx`
    - `AI Coding`
    - `Scaling`
    - `Refactor/Tech Debt`
- [ ] **Sourcing Scope** :
    - Priorité **US + Canada**.
    - Inclusion explicite des **Agencies/Consultancies**.

### Architecture & Points Clés (Pour le futur)
- **Enrichissement** : `enrich_prospects.py` est le cœur du système. Il nettoie les noms, extrait les métadonnées (Skills, Exp) et applique les tags.
- **Backfill** : Un script de maintenance (`backfill_segments.py`) existe pour ré-analyser la base existante si les règles de segmentation changent.
- **Extensibilité** : La table `Tags` est générique. On pourra ajouter des tags "Interested", "Replied", "VIP" sans changer le schéma.

---

## Phase 2 : Messagerie Autonome (Sans Apify)
**Objectif :** Réduire les coûts et gagner en contrôle en gérant l'envoi et la réception de messages via le navigateur (Playwright) directement, sans passer par Apify pour les DMs.

### 2.1 Moteur de Scraping de Chat (`chat_scraper.py`)
- [ ] Créer un script Playwright qui :
    - Se connecte sur LinkedIn.
    - Ouvre la messagerie.
    - Scrolle pour charger les conversations récentes.
    - Extrait : Nom de l'interlocuteur, Dernier message, Date, *Qui* a envoyé le dernier message (Moi vs Eux).
- [ ] Stocker ces conversations dans une nouvelle table `Conversations` et `Messages`.

### 2.2 Détection de Réponse (The Listener)
- [ ] Créer une tâche cron (`check_inbox.py`) qui tourne toutes les 30 min.
- [ ] Logique : Si un prospect a un nouveau message entrant -> Changer son statut de `messaged` à `replied` -> Stopper les séquences de relance auto.

---

## Phase 3 : Séquençage Avancé & Closing AI
**Objectif :** Implémenter une logique de "Drip Campaign" où l'IA gère les réponses et tente de closer le deal de manière autonome.

### 3.1 Moteur de Campagne & IA (`campaign_runner.py`)
- [ ] **Logique de Séquence** :
    - Step 1: Connection Request + Note.
    - Step 2: DM1 (Message de bienvenue).
    - Step 3: Wait 48h -> FU1.
    - Step 4: Wait +5-7 days -> FU2.
- [ ] **IA Autonomous Responder** :
    - À chaque réponse du prospect, l'IA analyse le sentiment.
    - **Context Injecté à l'IA** :
        - **Objectif de l'étape** : (ex: "Obtenir validation du problème").
        - **Historique Conversation** : Tous les messages précédents.
        - **Date Actuelle** : Pour proposer des créneaux cohérents.
        - **Link Calendly** : L'outil final pour le closing (Rdv 15 min).
    - **Prompt par Étape** : Chaque étape de la discussion aura un prompt spécifique (ex: "Phase Découverte", "Phase Closing", "Phase Objection").
    - **Objectif Final** : Amener le prospect à booker un meeting de 15 min via le lien Calendly.

### 3.3 Stratégie de Contenu (Client Brief)
**Default Outreach Copy** :
- **Connection Note** : "Quick question — seeing AI/agentic coding hit limits because of codebase constraints or delivery feedback loops?"
- **DM1** : "In your org, what breaks first when pushing agentic coding: codebase structure/boundaries, slow feedback loops (tests/build), review/approval flow, or dev environments/tooling?"
- **FU1 (+48h)** : "Curious which one is the main bottleneck on your side right now?"
- **FU2 (+5-7 days)** : "Last ping — if it’s relevant, happy to compare notes briefly (12–15 mins). If not, no worries."

**Règles de Gestion AI** :
- **Pre-qual Question** : L'IA doit absolument qualifier le lead sur les points ci-dessus (Codebase / Loop / Review / Env).
- **Max Follow-ups** : 3 max après DM1 si pas de réponse.
- **Gestion "Not Now"** : Demander "When to circle back?" puis arrêter.
- **Tagging** : Taguer chaque réponse significative (Pain / Objection / Timing / Not ICP).

### 3.4 Interface de Gestion
- [ ] UI pour configurer les Prompts Système de chaque étape.
- [ ] Configuration des délais et des conditions de passage d'étape.

---

## Phase 4 : Interface de Chat & Monitoring (Le "Cockpit")
**Objectif :** Une interface de supervision pour regarder l'IA travailler et reprendre la main *si nécessaire*.

### 4.1 Vue "Inbox" Unifiée (Monitoring)
- [ ] Créer une page `/inbox` style WhatsApp.
- [ ] **Live Feed** : Voir les messages envoyés par l'IA en temps réel.
- [ ] **Mode "Pilote Automatique"** : Indicateur visuel montrant que l'IA gère ce thread.

### 4.2 Reprise de Main (Human Takeover)
- [ ] Bouton **"Stop AI & Take Over"** : Désactive l'IA pour ce prospect spécifique si l'humain détecte un problème.
- [ ] L'opérateur peut alors répondre manuellement.
- [ ] Tags automatiques de statut : `AI_HANDLING`, `HUMAN_INTERVENTION`, `MEETING_BOOKED`.

---

## Phase 5 : Reporting & Ops
**Objectif :** Suivre les KPIs précis demandés (Taux de réponse par segment, A/B Testing).

### 5.1 Dashboard Analytique
- [ ] KPIs clés (Client Requirements) :
    - # Invites Sent vs Accepted.
    - # Replies.
    - # **Qualified** (Réponses sur le pain point).
    - # **Calls Booked**.
    - **Top Objections & Pains** (Analysés par l'IA dans les notes).
    - **Performance A/B Segment** : "Le Segment A (11-100) répond à 12%".
    - **Performance Hook** : Quel message d'intro génère le plus de réponses ?

### 5.2 Export & Weekly Report
- [ ] Génération automatique d'un rapport (JSON/CSV) avec les metrics de la semaine pour faciliter le "2x per week update".

---

## Résumé du Planning Suggéré
1.  **Semaine 1** : Phase 1 (Data/Tags) + Phase 2 (Scraping Messagerie sans Apify).
2.  **Semaine 2** : Phase 3 (Moteur de Séquences Complexe).
3.  **Semaine 3** : Phase 4 (Interface Inbox & Qualif).
4.  **Semaine 4** : Phase 5 (Reporting & Optimisation).
