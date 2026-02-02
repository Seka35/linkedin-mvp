# 🚀 Guide de Déploiement sur VPS (tbisla.pro)

## ✅ Prérequis

Tu as déjà :
- ✅ DNS configuré : `linkedin.tbisla.pro` pointe vers ton VPS
- ✅ Traefik qui tourne (avec n8n et mailcow)
- ✅ Docker et Docker Compose installés

## 📋 Étapes de Déploiement

### 1️⃣ Transférer les fichiers sur le VPS

Depuis ta machine locale, envoie le projet sur ton VPS :

```bash
# Option A : Via rsync (recommandé)
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
  /home/seka/Desktop/linkedin-mvp/ root@tbisla.pro:/opt/linkedin-bot/

# Option B : Via Git (si tu as déjà push sur GitHub)
# Sur le VPS :
cd /opt
git clone https://github.com/ton-username/linkedin-mvp.git linkedin-bot
cd linkedin-bot
```

### 2️⃣ Configurer les variables d'environnement

Sur le VPS, crée/édite le fichier `.env` :

```bash
cd /opt/linkedin-bot
nano .env
```

Assure-toi d'avoir toutes tes variables (API keys, credentials LinkedIn, etc.)

### 3️⃣ Créer les dossiers nécessaires

```bash
mkdir -p data logs
chmod 755 data logs
```

### 4️⃣ Construire et lancer le conteneur

```bash
# Construire l'image Docker
docker-compose build

# Lancer le conteneur
docker-compose up -d

# Vérifier les logs
docker-compose logs -f app
```

### 5️⃣ Vérifier que Traefik a bien détecté le service

```bash
# Voir les logs de Traefik
docker logs traefik

# Tu devrais voir quelque chose comme :
# "Router linkedin@docker created"
# "Service linkedin@docker created"
```

### 6️⃣ Tester l'accès

Attends 1-2 minutes que Let's Encrypt génère le certificat SSL, puis :

```bash
# Test depuis le VPS
curl -I https://linkedin.tbisla.pro

# Ou ouvre dans ton navigateur :
# https://linkedin.tbisla.pro
```

## 🔧 Commandes Utiles

### Voir les logs en temps réel
```bash
docker-compose logs -f app
```

### Redémarrer l'application
```bash
docker-compose restart app
```

### Arrêter l'application
```bash
docker-compose down
```

### Reconstruire après modifications
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Voir les conteneurs actifs
```bash
docker ps
```

### Accéder au shell du conteneur
```bash
docker exec -it linkedin_bot_app bash
```

## 🐛 Dépannage

### Le site n'est pas accessible

1. **Vérifier que le conteneur tourne :**
   ```bash
   docker ps | grep linkedin
   ```

2. **Vérifier les logs :**
   ```bash
   docker-compose logs app
   ```

3. **Vérifier que Traefik voit le service :**
   ```bash
   docker logs traefik | grep linkedin
   ```

4. **Vérifier le DNS :**
   ```bash
   nslookup linkedin.tbisla.pro
   # Doit pointer vers l'IP de ton VPS
   ```

### Erreur de certificat SSL

Traefik génère automatiquement le certificat. Si ça ne marche pas :

```bash
# Vérifier les logs Traefik
docker logs traefik

# Forcer la régénération (si nécessaire)
docker-compose down
docker-compose up -d
```

### Le conteneur redémarre en boucle

```bash
# Voir les logs pour identifier l'erreur
docker-compose logs app

# Problèmes courants :
# - Variables d'environnement manquantes dans .env
# - Problème avec Playwright (vérifier le Dockerfile)
# - Port déjà utilisé
```

## 📊 Architecture Réseau

```
Internet (HTTPS)
    ↓
Traefik (ports 80/443)
    ↓
linkedin.tbisla.pro → linkedin_bot_app:5000
n8n.tbisla.pro → n8n:5678
mail.tbisla.pro → nginx-mailcow:8080
```

## 🔐 Sécurité

- ✅ SSL/TLS automatique via Let's Encrypt
- ✅ Redirection HTTP → HTTPS
- ✅ Headers de sécurité (HSTS, XSS Protection, etc.)
- ✅ Isolation réseau Docker
- ⚠️ **Important** : Ne jamais exposer directement les ports (5000, etc.) - Traefik s'en charge

## 📝 Notes

- Le conteneur redémarre automatiquement (`restart: unless-stopped`)
- Les données sont persistées dans `./data` et `./logs`
- Le timezone est configuré sur `Europe/Paris`
- Playwright et Chromium sont installés dans le conteneur
