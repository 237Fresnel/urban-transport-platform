from faker import Faker
from pymongo import MongoClient
from cassandra.cluster import Cluster
import random
import uuid
from datetime import datetime, timedelta
from tqdm import tqdm

# Configuration
TOTAL_TRIPS    = 500_000
BATCH_SIZE     = 5_000
MONGO_URL      = "mongodb://localhost:27017"
CASSANDRA_HOST = "localhost"

fake    = Faker('fr_FR')
cities  = ["Paris", "Lyon", "Marseille", "Toulouse", "Bordeaux"]
zones   = ["Zone A", "Zone B", "Zone C", "Zone D", "Zone E"]

# Connexion MongoDB
print("Connexion à MongoDB...")
mongo_client = MongoClient(MONGO_URL)
db           = mongo_client["transport"]
collection   = db["trips"]

# Vider la collection si elle existe déjà
collection.drop()
print("MongoDB prêt")

# Connexion Cassandra 
print(" Connexion à Cassandra...")
cassandra_cluster = Cluster([CASSANDRA_HOST])
session           = cassandra_cluster.connect("transport")

# Vider les tables si elles existent déjà
session.execute("TRUNCATE trips_by_hour")
session.execute("TRUNCATE trips_by_zone")
print(" Cassandra prête")

# Requêtes préparées Cassandra 
# Les "prepared statements" sont plus rapides car Cassandra
# compile la requête une seule fois
insert_hour = session.prepare("""
    UPDATE trips_by_hour
    SET trip_count = trip_count + 1
    WHERE city = ? AND date = ? AND hour = ?
""")

insert_zone = session.prepare("""
    UPDATE trips_by_zone
    SET trip_count = trip_count + 1
    WHERE city = ? AND zone = ?
""")

# Génération des trajets
print(f"\n Génération de {TOTAL_TRIPS:,} trajets...\n")

batch_docs = []

for i in tqdm(range(TOTAL_TRIPS), unit=" trajets"):

    # Timestamp aléatoire sur les 365 derniers jours
    ts = datetime.now() - timedelta(
        days    = random.randint(0, 364),
        hours   = random.randint(0, 23),
        minutes = random.randint(0, 59)
    )

    city       = random.choice(cities)
    zone_start = random.choice(zones)
    zone_end   = random.choice(zones)
    date_str   = ts.strftime("%Y-%m-%d")

    # Document MongoDB
    trip = {
        "trip_id"    : str(uuid.uuid4()),
        "user_id"    : str(uuid.uuid4()),
        "city"       : city,
        "zone_start" : zone_start,
        "zone_end"   : zone_end,
        "distance_km": round(random.uniform(0.5, 50.0), 2),
        "price_eur"  : round(random.uniform(1.0, 25.0), 2),
        "timestamp"  : ts,
        "hour"       : ts.hour,
        "day_of_week": ts.strftime("%A"),
        "date"       : date_str
    }
    batch_docs.append(trip)

    # Cassandra — incrémenter les compteurs
    session.execute(insert_hour, (city, date_str, ts.hour))
    session.execute(insert_zone, (city, zone_start))

    # Insertion MongoDB par batch de 5000
    if len(batch_docs) == BATCH_SIZE:
        collection.insert_many(batch_docs)
        batch_docs = []

# Insérer le reste
if batch_docs:
    collection.insert_many(batch_docs)

# Index MongoDB pour accélérer les requêtes
print("\n Création des index MongoDB...")
collection.create_index("city")
collection.create_index("date")
collection.create_index("hour")
collection.create_index("timestamp")
collection.create_index([("city", 1), ("date", 1)])
print(" Index créés")

# Résumé final
total_mongo = collection.count_documents({})
print(f"\n Génération terminée !")
print(f"   MongoDB  : {total_mongo:,} trajets insérés")
print(f"   Cassandra: compteurs mis à jour")
print(f"   Index    : actifs\n")

# Fermeture des connexions
mongo_client.close()
cassandra_cluster.shutdown()