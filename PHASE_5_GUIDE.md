# 🎯 Phase 5 - Campagnes LinkedIn : Guide Complet

## 📋 Vue d'ensemble

Les campagnes te permettent d'automatiser complètement ton outreach LinkedIn :
1. **Scraping** de prospects
2. **Connexion/Follow** automatique
3. **Messages** automatiques après un délai

---

## 🔄 Comment ça fonctionne ?

### Étape 1 : Créer une campagne

1. Va sur **Campaigns** dans le menu
2. Clique sur **+ Nouvelle campagne**
3. Remplis le formulaire :
   - **Nom** : Ex: "CEO Paris SaaS Q1 2026"
   - **Requête** : Ex: "CEO Paris SaaS"
   - **Premier message** : Ex: "Bonjour {name}, j'ai vu votre profil..."
   - **Délai avant message** : Ex: 3 jours (le bot attendra 3 jours après connexion/follow avant d'envoyer le message)
   - **Limite/jour** : Ex: 10 (max 10 actions par jour pour cette campagne)

### Étape 2 : Scraper des prospects

1. Va sur le **Dashboard**
2. Dans la section "🔍 Rechercher des prospects"
3. Entre la **même requête** que ta campagne (ex: "CEO Paris SaaS")
4. Clique sur **Rechercher**
5. Le bot va :
   - Chercher sur Google/SearchAPI
   - Extraire les profils LinkedIn
   - Les ajouter à ta base de données avec le statut "new"

### Étape 3 : Le bot automatise tout

Le bot va maintenant (tu peux lancer manuellement ou via un cron job) :

1. **Connexion/Follow** :
   - Prend les prospects "new" de la campagne
   - Envoie des demandes de connexion (ou Follow si Connect n'est pas disponible)
   - Respecte la limite quotidienne (ex: 10/jour)
   - Change le statut en "connected" ou "followed"

2. **Attente** :
   - Le bot attend X jours (le délai que tu as défini, ex: 3 jours)

3. **Message automatique** :
   - Après 3 jours, le bot envoie automatiquement le "Premier message"
   - Change le statut en "messaged"
   - Enregistre l'action dans la base de données

---

## 📊 Suivi de campagne

Sur la page **Campaigns**, tu peux voir pour chaque campagne :
- Nombre de prospects scrapés
- Nombre de connexions envoyées
- Nombre de messages envoyés
- Statut (active, paused, completed)

---

## 🎯 Exemple concret

**Campagne : "CEO Paris SaaS"**

1. **Jour 1** :
   - Tu crées la campagne
   - Tu scrapes 20 prospects avec la requête "CEO Paris SaaS"
   - Le bot envoie 10 demandes de connexion/follow (limite quotidienne)

2. **Jour 2** :
   - Le bot envoie 10 autres demandes de connexion/follow

3. **Jour 4** (3 jours après Jour 1) :
   - Le bot envoie automatiquement le message aux 10 premiers prospects qui ont accepté/été suivis

4. **Jour 5** :
   - Le bot envoie le message aux 10 autres prospects

---

## ⚙️ Variables dans les messages

Tu peux utiliser des variables dans tes messages :
- `{name}` : Prénom du prospect
- `{full_name}` : Nom complet
- `{company}` : Entreprise
- `{title}` : Titre/poste

Exemple :
```
Bonjour {name},

J'ai vu que vous êtes {title} chez {company}. 
Je serais ravi d'échanger avec vous sur...

Cordialement
```

---

## 🚀 Prochaines étapes

1. **Teste avec une petite campagne** (5-10 prospects)
2. **Vérifie les résultats** sur /messages
3. **Ajuste tes messages** selon les réponses
4. **Scale progressivement** (20, 50, 100+ prospects)

---

## ⚠️ Bonnes pratiques

- **Limite quotidienne** : Ne dépasse pas 50 actions/jour pour éviter les restrictions LinkedIn
- **Délai avant message** : Minimum 2-3 jours pour paraître naturel
- **Personnalisation** : Utilise les variables pour personnaliser tes messages
- **Suivi** : Vérifie régulièrement /messages pour voir les réponses

---

## 🔧 Automatisation (Optionnel)

Pour automatiser complètement, tu peux créer un cron job qui lance le bot tous les jours :

```bash
# Cron job : tous les jours à 10h
0 10 * * * cd /home/seka/Desktop/linkedin-mvp && ./venv/bin/python run_campaigns.py
```

Le script `run_campaigns.py` va :
1. Charger toutes les campagnes "active"
2. Pour chaque campagne :
   - Envoyer des connexions aux prospects "new" (limite quotidienne)
   - Envoyer des messages aux prospects connectés depuis X jours
3. Logger toutes les actions

---

✅ **Phase 5 terminée !** Tu as maintenant un système complet d'automatisation LinkedIn.
