# 🚌 Urban Transport Analytics

Plateforme Big Data d'analyse de transport urbain simulant 500 000 trajets sur 5 villes françaises, combinant MongoDB, Cassandra et Apache Spark pour le stockage et l'analyse distribuée, exposée via une API FastAPI et visualisée sur un dashboard React.

---

## Stack technique

| Couche | Technologie |
|---|---|
| Stockage document | MongoDB 7 |
| Stockage temporel | Cassandra 4.1 |
| Traitement batch | Apache Spark 3.5 |
| API REST | FastAPI (Python) |
| Frontend | React + TypeScript + Recharts |
| Conteneurisation | Docker + Docker Compose |
| Reverse proxy | Nginx |

---

## Structure du projet

```
urban-transport-platform/
├── data-generator/       # Script Python de génération des 500 000 trajets
├── api/                  # Backend FastAPI
├── frontend/             # Dashboard React
├── spark-jobs/           # Jobs d'analyse batch Spark
│   └── output/           # Résultats JSON des analyses
├── nginx/                # Config reverse proxy
└── docker-compose.yml
```

---

## Prérequis

- Docker et Docker Compose installés
- Python 3.10+
- Node.js 18+

---

## Lancer le projet en local

```bash
# 1. Cloner le repo
git clone https://github.com/ton-username/urban-transport-platform.git
cd urban-transport-platform

# 2. Lancer tous les services
docker compose up -d

# 3. Vérifier que tout tourne
docker compose ps
```

Une fois lancé :

```
http://localhost          → Dashboard React
http://localhost/api/docs → Documentation API interactive
http://localhost:8080     → Interface Spark
```

---

## Générer les données

```bash
cd data-generator
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python generate.py
```

---

## Lancer les analyses Spark

```bash
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.mongodb.spark:mongo-spark-connector_2.12:10.3.0 \
  /opt/spark-jobs/analytics.py
```

---

## Endpoints API

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/health` | Statut de l'API |
| GET | `/cities` | Liste des villes |
| GET | `/stats/daily` | Trajets par jour |
| GET | `/stats/hourly` | Heures de pointe |
| GET | `/stats/cities` | Distance moyenne par ville |
| GET | `/stats/weekday` | Activité par jour de semaine |
| GET | `/top-zones` | Zones les plus fréquentées |
| GET | `/trips` | Liste filtrée des trajets |

---

## Déploiement cloud (gratuit)

| Service | Plateforme |
|---|---|
| Base de données | MongoDB Atlas (M0 Free) |
| API | Render.com |
| Frontend | Vercel |

---

## Arrêter le projet

```bash
docker compose down
```


