# 🔍 Debug du Scraping sur VPS

## Problème
Le scraping retourne 0 résultats alors que l'application fonctionne.

## Vérifications à faire

### 1. Vérifier les logs de l'application
```bash
# Sur le VPS
docker-compose logs app --tail 100

# Chercher les erreurs de scraping
docker-compose logs app | grep -i "error\|exception\|apify\|serp"
```

### 2. Vérifier que le .env est bien monté
```bash
# Entrer dans le conteneur
docker exec -it linkedin_bot_app bash

# Vérifier si le .env existe
ls -la /app/.env

# Voir le contenu (masquer les vraies clés)
cat /app/.env | grep -v "PASSWORD\|KEY\|SECRET"

# Sortir
exit
```

### 3. Vérifier les variables d'environnement
```bash
docker exec -it linkedin_bot_app env | grep -E "APIFY|SERP|OPENROUTER"
```

## Solutions possibles

### Solution 1 : Le .env n'est pas monté
Le problème est que le `.env` n'est **pas copié dans le conteneur** car il est dans `.dockerignore`.

**Fix** : Ajouter un volume dans docker-compose.yml
```yaml
volumes:
  - ./data:/app/data
  - ./logs:/app/logs
  - ./.env:/app/.env  # ← Ajouter cette ligne
```

### Solution 2 : Les API keys sont invalides
Vérifier que les vraies clés API sont dans `/opt/linkedin-mvp/.env` sur le VPS :
- `APIFY_API_KEY`
- `SERP_API_KEY`
- `OPENROUTER_KEY`

### Solution 3 : Passer les variables via docker-compose
Au lieu de monter le .env, passer les variables directement dans docker-compose.yml :
```yaml
environment:
  - FLASK_ENV=production
  - PYTHONUNBUFFERED=1
  - TZ=Europe/Paris
  - APIFY_API_KEY=${APIFY_API_KEY}
  - SERP_API_KEY=${SERP_API_KEY}
  - OPENROUTER_KEY=${OPENROUTER_KEY}
```

## Commandes de test

```bash
# Tester l'API Apify depuis le conteneur
docker exec -it linkedin_bot_app python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('APIFY_API_KEY:', os.getenv('APIFY_API_KEY', 'NOT FOUND'))
print('SERP_API_KEY:', os.getenv('SERP_API_KEY', 'NOT FOUND'))
"
```
