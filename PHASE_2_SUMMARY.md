# PHASE 2 SUMMARY : DATABASE & AUTH MODELS

## Ce qui a été fait
- **Modèles de base de données** (`database/models.py`) :
  - `Prospect` : Stockage des prospects (url, nom, status...).
  - `Campaign` : Gestion des campagnes et templates de messages.
  - `Action` : Historique des actions (visites, ajouts, messages).
  - Relations `Foreign Key` établies entre les tables.
- **Connexion Database** (`database/db.py`) :
  - Utilisation directe de SQLAlchemy (`create_engine`, `sessionmaker`) pour plus de flexibilité.
  - Fonction `init_db()` qui crée automatiquement les tables si elles n'existent pas.
  - Fichier de base de données : `data/prospects.db`.
- **Intégration** :
  - `main.py` initialise la base de données au démarrage.
  - Le système est prêt à recevoir des données.

## Note sur l'Authentification (Cookie)
Comme remarqué par l'utilisateur, l'authentification bot (Phase 4) se fera par **cookie de session** (`li_at`) et non par login/mdp.
- Les modèles actuels sont compatibles (pas de stockage de credentials user en base).
- Le cookie sera géré via `.env` et injecté dans Playwright lors de la Phase 4.

## Instructions pour l'IA suivante (PHASE 3)
**Objectif :** Implémenter le Scraping (Google SERP & Profils LinkedIn).

1.  **Service Scraper** (`services/scraper.py`) :
    - Implémenter la recherche de profils.
    - Soit via API externe (Google Search API / Apify).
    - Soit via scraping manuel Google (attention aux blocages).
2.  **Stockage** :
    - Sauvegarder les résultats de scraping dans la table `Prospect`.
    - Éviter les doublons (`linkedin_url` est unique).
3.  **Test** :
    - Créer un script pour tester l'ajout d'un prospect en base.
