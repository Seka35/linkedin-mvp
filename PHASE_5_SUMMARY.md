# PHASE 5 SUMMARY : WEB INTERFACE (FLASK)

## Ce qui a été fait
- **Backend Flask** (`web/app.py`) :
  - Routes implémentées : `/` (Dashboard), `/prospects`, `/campaigns`.
  - API Routes : `/api/scrape`, `/api/connect`, `/api/message` qui connectent le frontend aux services Python.
  - Le serveur tourne sur le port 5000.
- **Frontend** :
  - Templates HTML créés avec héritage (`base.html`).
  - Style CSS style LinkedIn (`style.css`).
  - JS pour les appels API asynchrones (AJAX) et feedback utilisateurs.
- **Fonctionnalités disponibles via UI** :
  - Dashboard (Stats + Recherche Google/LinkedIn).
  - Liste des prospects avec filtres.
  - Boutons d'action : Connexion, Message (qui lancent le bot en arrière-plan).
  - Création de campagnes.

## Instructions pour l'IA suivante (PHASE 6)
**Objectif :** Implémenter le moteur de Campagnes (Séquences Automatiques).

1.  **Service Campagne** (`services/campaign_runner.py`) :
    - Créer un script capable de traiter une campagne active.
    - Pour chaque prospect "NEW" de la campagne :
      - Envoyer une connexion.
      - Mettre à jour le statut.
      - Respecter la limite journalière (`daily_limit`).
2.  **Scheduler** (Optionnel pour MVP, ou bouton "Lancer Campagne") :
    - Ajouter un endpoint/bouton pour exécuter le traitement des campagnes.
3.  **Logs & Suivi** :
    - Enregistrer chaque action dans la table `Action`.
