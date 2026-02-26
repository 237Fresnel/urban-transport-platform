from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
import json
import os

load_dotenv()

# Initialisation 
app = FastAPI(
    title="Urban Transport API",
    description="API d'analyse des données de transport urbain",
    version="1.0.0"
)

# CORS — permet au frontend React d'appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Connexion MongoDB 
MONGO_URL = os.getenv("MONGO_ATLAS_URL") or os.getenv("MONGO_URL", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["transport"]

# Dossier des résultats Spark 
SPARK_OUTPUT = os.getenv("SPARK_OUTPUT", "../spark-jobs/output")

def load_spark_result(filename: str):
    """Charge un fichier JSON produit par Spark"""
    path = os.path.join(SPARK_OUTPUT, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

# Routes 

@app.get("/")
def root():
    return {
        "message": "Urban Transport API",
        "version": "1.0.0",
        "endpoints": [
            "/stats/daily",
            "/stats/hourly",
            "/stats/cities",
            "/top-zones",
            "/trips",
            "/cities",
            "/health"
        ]
    }

@app.get("/health")
def health():
    """Vérifie que l'API et MongoDB sont opérationnels"""
    try:
        mongo_client.admin.command("ping")
        mongo_status = "ok"
    except Exception as e:
        mongo_status = f"error: {str(e)}"

    return {
        "api": "ok",
        "mongodb": mongo_status
    }

@app.get("/stats/daily")
def daily_stats(city: str = Query(None, description="Filtrer par ville")):
    """
    Retourne le nombre de trajets par jour.
    Utilise les résultats Spark si disponibles,
    sinon interroge MongoDB directement.
    """
    # Essayer d'abord les résultats Spark (plus rapide)
    spark_data = load_spark_result("daily.json")
    if spark_data:
        if city:
            # Filtrer par ville depuis MongoDB si Spark n'a pas ce filtre
            pipeline = [
                {"$match": {"city": city}},
                {"$group": {"_id": "$date", "trip_count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
                {"$project": {"date": "$_id", "trip_count": 1, "_id": 0}}
            ]
            return list(db.trips.aggregate(pipeline))
        return spark_data

    # Fallback MongoDB
    pipeline = []
    if city:
        pipeline.append({"$match": {"city": city}})
    pipeline += [
        {"$group": {"_id": "$date", "trip_count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
        {"$project": {"date": "$_id", "trip_count": 1, "_id": 0}}
    ]
    return list(db.trips.aggregate(pipeline))


@app.get("/stats/hourly")
def hourly_stats(city: str = Query(None, description="Filtrer par ville")):
    """Retourne le nombre de trajets par heure (heures de pointe)"""
    spark_data = load_spark_result("rush_hours.json")
    if spark_data and not city:
        return spark_data

    pipeline = []
    if city:
        pipeline.append({"$match": {"city": city}})
    pipeline += [
        {"$group": {"_id": "$hour", "trip_count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
        {"$project": {"hour": "$_id", "trip_count": 1, "_id": 0}}
    ]
    return list(db.trips.aggregate(pipeline))


@app.get("/stats/cities")
def cities_stats():
    """Retourne la distance moyenne et le nombre de trajets par ville"""
    spark_data = load_spark_result("avg_distance.json")
    if spark_data:
        return spark_data

    pipeline = [
        {"$group": {
            "_id": "$city",
            "avg_distance": {"$avg": "$distance_km"},
            "trip_count": {"$sum": 1}
        }},
        {"$sort": {"trip_count": -1}},
        {"$project": {
            "city": "$_id",
            "avg_distance": {"$round": ["$avg_distance", 2]},
            "trip_count": 1,
            "_id": 0
        }}
    ]
    return list(db.trips.aggregate(pipeline))


@app.get("/top-zones")
def top_zones(limit: int = Query(10, description="Nombre de zones à retourner")):
    """Retourne les zones de départ les plus fréquentées"""
    spark_data = load_spark_result("top_zones.json")
    if spark_data:
        return spark_data[:limit]

    pipeline = [
        {"$group": {"_id": "$zone_start", "trip_count": {"$sum": 1}}},
        {"$sort": {"trip_count": -1}},
        {"$limit": limit},
        {"$project": {"zone": "$_id", "trip_count": 1, "_id": 0}}
    ]
    return list(db.trips.aggregate(pipeline))


@app.get("/trips")
def get_trips(
    city: str = Query(None, description="Filtrer par ville"),
    date: str = Query(None, description="Filtrer par date (YYYY-MM-DD)"),
    limit: int = Query(100, le=1000, description="Nombre max de résultats")
):
    """Retourne une liste filtrée de trajets"""
    query = {}
    if city:
        query["city"] = city
    if date:
        query["date"] = date

    trips = list(db.trips.find(query, {"_id": 0}).limit(limit))
    return trips


@app.get("/cities")
def get_cities():
    """Retourne la liste des villes disponibles"""
    return db.trips.distinct("city")


@app.get("/stats/weekday")
def weekday_stats():
    """Retourne l'activité par jour de semaine et par ville"""
    spark_data = load_spark_result("by_day_of_week.json")
    if spark_data:
        return spark_data

    pipeline = [
        {"$group": {
            "_id": {"city": "$city", "day": "$day_of_week"},
            "trip_count": {"$sum": 1}
        }},
        {"$project": {
            "city": "$_id.city",
            "day_of_week": "$_id.day",
            "trip_count": 1,
            "_id": 0
        }}
    ]
    return list(db.trips.aggregate(pipeline))