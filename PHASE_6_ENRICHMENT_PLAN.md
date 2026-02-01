# 💎 Phase 6-B : Enrichissement des Données via Apify

**Objectif** : Transformer les prospects "basiques" (récupérés via Google) en profils complets (Email, Expérience, Bio) sans risquer le compte LinkedIn de l'utilisateur.

---

## 📅 Étape 1 : Base de Données (`models.py`)

Ajouter les colonnes suivantes à la table `Prospect` :

```python
is_enriched = Column(Boolean, default=False)
summary = Column(Text)          # La section "Infos" / Bio
email = Column(String)          # Si disponible
phone = Column(String)          # Si disponible
skills = Column(Text)           # Stocké en JSON str: ["Python", "Sales", ...]
experiences = Column(Text)      # Stocké en JSON str: [{"company": "Google", "role": "CEO"...}, ...]
education = Column(Text)        # Stocké en JSON str
languages = Column(Text)        # Stocké en JSON str
```

---

## 🧠 Étape 2 : Service Backend (`services/apify_enrichment.py`)

Créer un service qui utilise l'API Apify (Actor: `linkedin-profile-scraper` ou similaire).

**Logique :**
1. Recevoir une liste d'IDs de prospects.
2. Extraire leurs `linkedin_url`.
3. Envoyer les URLs à Apify.
4. Attendre et récupérer les résultats JSON.
5. Parser les résultats (map Apify JSON -> DB Fields).
6. Sauvegarder et marquer `is_enriched = True`.

**Simulateur de coût** :
- Apify coûte des crédits. On ajoutera une estimation avant lancement.

---

## 💻 Étape 3 : Interface Utilisateur (`web/templates/`)

### A. Liste des Prospects (`prospects.html`)
- Ajouter une colonne/icône "💎" pour indiquer si le profil est enrichi.
- Ajouter un bouton global **"Enrichir la sélection"**.

### B. Vue Détillée (`prospect_modal.html`)
- Créer une belle Modale ou Page dédiée pour chaque prospect.
- Afficher :
  - Photo en grand + Header
  - 📧 Email / Téléphone
  - 📝 Résumé (About)
  - 💼 Timeline des expériences (Design vertical propre)
  - 🎓 Éducation

---

## 🔗 Étape 4 : API Endpoints (`web/app.py`)

- `POST /api/enrich`: Prend une liste d'IDs -> Lance le job Apify en arrière-plan.
- `GET /api/prospect/<id>`: Renvoie toutes les infos détaillées (pour la modale).

---

## ✅ Avantages Sécurité
- **ZERO risque pour ton compte LinkedIn**. C'est le proxy d'Apify qui visite les profils.
- Permet de filtrer intelligemment AVANT d'envoyer une connexion (ex: "Je ne contacte que ceux qui ont 'SaaS' dans leur résumé").
