from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, round as spark_round
import json
import os

# Initialisation de Spark
# On connecte Spark à MongoDB via le connecteur officiel
spark = SparkSession.builder \
    .appName("TransportAnalytics") \
    .config("spark.mongodb.read.connection.uri",
            "mongodb://mongodb:27017/transport.trips") \
    .config("spark.jars.packages",
            "org.mongodb.spark:mongo-spark-connector_2.12:10.3.0") \
    .getOrCreate()

# Réduire les logs pour plus de lisibilité
spark.sparkContext.setLogLevel("WARN")

print(" Spark connecté à MongoDB")

# Chargement des données 
# Spark lit toute la collection MongoDB en un DataFrame distribué
df = spark.read \
    .format("mongodb") \
    .option("spark.mongodb.read.connection.uri",
            "mongodb://mongodb:27017") \
    .option("spark.mongodb.read.database", "transport") \
    .option("spark.mongodb.read.collection", "trips") \
    .load()

df.cache()  # Garde les données en mémoire pour accélérer les analyses

total = df.count()
print(f" {total:,} trajets chargés dans Spark\n")

output_dir = "/opt/spark-jobs/output"
os.makedirs(output_dir, exist_ok=True)

# Analyse 1 : Trajets par jour 
print(" Analyse 1 : Trajets par jour...")

daily = df.groupBy("date") \
          .agg(count("*").alias("trip_count")) \
          .orderBy("date")

daily_list = [{"date": r["date"], "trip_count": r["trip_count"]}
              for r in daily.collect()]

with open(f"{output_dir}/daily.json", "w") as f:
    json.dump(daily_list, f, indent=2)

print(f"   → {len(daily_list)} jours analysés")

# Analyse 2 : Distance moyenne par ville 
print(" Analyse 2 : Distance moyenne par ville...")

avg_dist = df.groupBy("city") \
             .agg(spark_round(avg("distance_km"), 2).alias("avg_distance"),
                  count("*").alias("trip_count")) \
             .orderBy("avg_distance", ascending=False)

avg_list = [{"city": r["city"],
             "avg_distance": float(r["avg_distance"]),
             "trip_count": r["trip_count"]}
            for r in avg_dist.collect()]

with open(f"{output_dir}/avg_distance.json", "w") as f:
    json.dump(avg_list, f, indent=2)

print(f"   → {len(avg_list)} villes analysées")

# Analyse 3 : Heures de pointe 
print(" Analyse 3 : Heures de pointe...")

rush = df.groupBy("hour") \
         .agg(count("*").alias("trip_count")) \
         .orderBy("hour")

rush_list = [{"hour": r["hour"], "trip_count": r["trip_count"]}
             for r in rush.collect()]

with open(f"{output_dir}/rush_hours.json", "w") as f:
    json.dump(rush_list, f, indent=2)

print(f"   → 24 heures analysées")

# Analyse 4 : Top zones les plus fréquentées 
print(" Analyse 4 : Top zones...")

top_zones = df.groupBy("zone_start") \
              .agg(count("*").alias("trip_count")) \
              .orderBy("trip_count", ascending=False)

zones_list = [{"zone": r["zone_start"], "trip_count": r["trip_count"]}
              for r in top_zones.collect()]

with open(f"{output_dir}/top_zones.json", "w") as f:
    json.dump(zones_list, f, indent=2)

print(f"   → {len(zones_list)} zones analysées")

# Analyse 5 : Trajets par ville et jour de semaine 
print(" Analyse 5 : Trajets par ville et jour de semaine...")

by_day = df.groupBy("city", "day_of_week") \
           .agg(count("*").alias("trip_count")) \
           .orderBy("city", "trip_count", ascending=False)

day_list = [{"city": r["city"],
             "day_of_week": r["day_of_week"],
             "trip_count": r["trip_count"]}
            for r in by_day.collect()]

with open(f"{output_dir}/by_day_of_week.json", "w") as f:
    json.dump(day_list, f, indent=2)

print(f"   → {len(day_list)} combinaisons analysées")

#  Résumé 
print("\n Toutes les analyses sont terminées !")
print(f"   Fichiers écrits dans : {output_dir}/")
print("   - daily.json")
print("   - avg_distance.json")
print("   - rush_hours.json")
print("   - top_zones.json")
print("   - by_day_of_week.json")

spark.stop()