# PHASE 3 SUMMARY : SCRAPING SERVICE

## Ce qui a été fait
- **Service Scraper** (`services/scraper.py`) :
  - Intégration de **SearchAPI.io** (via `SERP_API_KEY`) pour scraper Google de manière fiable.
  - Fallback sur **DuckDuckGo** (HTML scraping) si l'API échoue.
  - Support de **Apify** intégré (si `APIFY_API_KEY` présent).
  - Déduplication automatique des URLs trouvées.
- **Stockage Database** :
  - Les prospects trouvés sont automatiquement sauvegardés dans la table `Prospect`.
  - Vérification d'existence avant insertion (pas de doublons `linkedin_url`).
- **Test Validé** :
  - Recherche "CEO startup Paris" réussie via SearchAPI.io.
  - 5 profils récupérés et stockés en base.

## Notes Techniques
- **Clés API** : `SERP_API_KEY` et `APIFY_API_KEY` sont gérées via `.env`.
- Le scraper extrait automatiquement le nom depuis l'URL si non disponible (via `_extract_name_from_url`).
- Les headers HTTP sont configurés pour éviter les blocages basiques.

## Instructions pour l'IA suivante (PHASE 4)
**Objectif :** Implémenter le Bot d'Automatisation (Playwright).

1.  **Authentification** : 
    - Utiliser la méthode **Cookie Session** (`li_at`) comme demandé par l'utilisateur.
    - Ne PAS implémenter le login email/password.
2.  **Service Bot** (`services/linkedin_bot.py`) :
    - Initialiser Playwright avec le cookie.
    - Implémenter `visit_profile(url)`.
    - Implémenter `send_connection(url, message)`.
3.  **Sécurité** :
    - Ajouter des délais aléatoires (human-like behavior).
    - Gérer les erreurs de navigation.
