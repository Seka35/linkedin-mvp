./venv/bin/python main.py

cd /opt/linkedin-mvp
git pull origin main

# Reconstruire pour être sûr que tout est propre
docker-compose down
docker-compose build --no-cache app
docker-compose up -d

# Tester
curl -I https://linkedin.tbisla.pro