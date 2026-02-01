# 🎯 Phase 5 - TERMINÉE ! Script d'automatisation créé

## ✅ Ce qui a été fait

### 1. Base de données mise à jour
- ✅ Ajout du champ `campaign_id` dans la table `Prospect` pour tagger les prospects
- ✅ Ajout du champ `message_delay_days` dans la table `Campaign`
- ✅ Relation bidirectionnelle entre `Prospect` et `Campaign`

### 2. Formulaire de campagne amélioré
- ✅ Supprimé le champ "Message de connexion" (inutile)
- ✅ Ajouté le champ "Délai avant message" (0-30 jours)
- ✅ Premier message obligatoire

### 3. Script d'automatisation créé : `run_campaigns.py`

**Fonctionnalités :**
- ✅ **Délais aléatoires** entre chaque action (30-120s pour connexions, 60-180s pour messages)
- ✅ **Tag automatique** : Les prospects sont taggés avec `campaign_id` quand ils sont contactés
- ✅ **Prend TOUS les prospects "new"** (pas juste ceux de la campagne)
- ✅ **Envoie des connexions/follow** avec délais aléatoires
- ✅ **Envoie des messages après X jours** automatiquement
- ✅ **Personnalisation des messages** avec variables {name}, {full_name}, {company}, {title}

---

## 🚀 Comment utiliser

### Étape 1 : Créer une campagne

1. Va sur http://127.0.0.1:5000/campaigns
2. Clique sur "+ Nouvelle campagne"
3. Remplis :
   - Nom : "CEO Paris SaaS Q1"
   - Requête : "CEO Paris SaaS"
   - Message : "Bonjour {name}, j'ai vu votre profil..."
   - Délai : 3 jours
   - Limite : 10/jour

### Étape 2 : Scraper des prospects

1. Va sur le Dashboard
2. Entre la requête : "CEO Paris SaaS"
3. Clique sur "Rechercher"
4. Les prospects sont ajoutés avec statut "new"

### Étape 3 : Lancer le script d'automatisation

**Manuellement :**
```bash
cd /home/seka/Desktop/linkedin-mvp
./venv/bin/python run_campaigns.py
```

**Automatiquement (Cron job) :**
```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour lancer tous les jours à 10h
0 10 * * * cd /home/seka/Desktop/linkedin-mvp && ./venv/bin/python run_campaigns.py >> /tmp/linkedin_campaigns.log 2>&1
```

---

## 🎯 Ce que fait le script

### Étape 1 : Connexions/Follow (avec délais aléatoires)

1. Récupère les 10 premiers prospects "new" (limite de la campagne)
2. Pour chaque prospect :
   - Envoie connexion/follow
   - **Tag le prospect** avec `campaign_id`
   - Change le statut en "connected" ou "followed"
   - **Attend 30-120 secondes** (aléatoire) avant le suivant
3. Enregistre toutes les actions dans la DB

### Étape 2 : Messages automatiques

1. Récupère les prospects de la campagne connectés/followed depuis 3+ jours
2. Filtre ceux qui n'ont pas encore reçu de message
3. Pour chaque prospect :
   - Personnalise le message ({name}, {company}, etc.)
   - Envoie le message
   - Change le statut en "messaged"
   - **Attend 60-180 secondes** (aléatoire) avant le suivant
4. Enregistre toutes les actions dans la DB

---

## 📊 Exemple de timeline

**Jour 1 (10h00)** :
- Script lancé
- 10 prospects "new" trouvés
- Connexions envoyées avec délais aléatoires (total ~15 minutes)
- Prospects taggés avec la campagne

**Jour 2 (10h00)** :
- Script lancé
- 10 autres prospects "new" trouvés
- Connexions envoyées

**Jour 4 (10h00)** :
- Script lancé
- Les 10 premiers prospects (Jour 1) sont connectés depuis 3 jours
- Messages envoyés automatiquement avec délais aléatoires (total ~25 minutes)

---

## ⚠️ Sécurité anti-détection

Le script inclut plusieurs mécanismes pour éviter la détection LinkedIn :

1. **Délais aléatoires** :
   - Connexions : 30-120 secondes entre chaque
   - Messages : 60-180 secondes entre chaque

2. **Limite quotidienne** respectée (10/jour par défaut)

3. **Délai avant message** (3 jours par défaut)

4. **Headless mode** : Le bot tourne en arrière-plan

---

## 🔧 Prochaines améliorations possibles

1. **Auto-scraping** : Si pas assez de prospects "new", lancer automatiquement le scraping
2. **Statistiques de campagne** : Afficher sur /campaigns le nombre de prospects, connexions, messages
3. **Pause/Resume** : Pouvoir mettre en pause une campagne
4. **Suivi des réponses** : Détecter quand un prospect répond

---

## ✅ Phase 5 TERMINÉE !

Tu as maintenant un système complet d'automatisation LinkedIn avec :
- ✅ Scraping de prospects
- ✅ Connexions/Follow automatiques avec délais aléatoires
- ✅ Messages automatiques après X jours
- ✅ Tagging des prospects par campagne
- ✅ Logging complet de toutes les actions

**Prochaine étape** : Tester avec une vraie campagne ! 🚀
