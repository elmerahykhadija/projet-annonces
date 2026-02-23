import sys
import os
import subprocess
import threading
import time

# Fix encodage pour l'affichage sur Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# --- 1. Lancement du Producer2 (MarocAnnonces) ---
def start_producer(script_name):
    """Lance un script producer dans un processus séparé"""
    try:
        print(f"🚀 Démarrage du producer: {script_name}")
        process = subprocess.Popen(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=1
        )
        
        def log_output(pipe, prefix):
            for line in iter(pipe.readline, ''):
                if line.strip():
                    print(f"[{prefix}] {line.strip()}")
        
        threading.Thread(target=log_output, args=(process.stdout, script_name), daemon=True).start()
        threading.Thread(target=log_output, args=(process.stderr, f"{script_name}-ERR"), daemon=True).start()
        
        return process
    except Exception as e:
        print(f"❌ Erreur démarrage {script_name}: {e}")
        return None

print("\n" + "="*70)
print("🎯 SPARK JOB MAROCANNONCES - DÉMARRAGE")
print("="*70)

producer_process = start_producer("producers/producer2.py")

if producer_process:
    print(f"✅ Producer2 (MarocAnnonces) lancé - PID: {producer_process.pid}")
else:
    print("⚠️  Producer2 n'a pas démarré")
    sys.exit(1)

print("\n⏳ Attente de 10 secondes pour initialisation...\n")
time.sleep(10)

# --- 2. Configuration Spark ---
spark = SparkSession.builder \
    .appName("MarocAnnoncesProcessor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.mysql:mysql-connector-j:8.2.0") \
    .config("spark.sql.streaming.checkpointLocation", "./checkpoint_marocannonces") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# --- 3. Schéma ---
schema = StructType([
    StructField("source", StringType()),
    StructField("category", StringType()),
    StructField("sous_categorie", StringType()),
    StructField("titre", StringType()),
    StructField("prix", StringType()),
    StructField("localisation", StringType()),
    StructField("url", StringType()),
    StructField("image_url", StringType()),
    StructField("date_text", StringType()),
    StructField("timestamp", DoubleType())
])

# --- 4. Lecture Kafka ---
# ✅ Correction : Utilisation de 'earliest' pour ne rien rater au démarrage
df_kafka = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "annonces-raw") \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false") \
    .load()

# --- 5. Transformation ---
df_parsed = df_kafka.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

# ✅ Correction : Suppression des doublons au sein du batch Spark pour éviter Duplicate Entry
df_clean = df_parsed.withColumn("timestamp_scraped", col("timestamp").cast("long")) \
                    .drop("timestamp") \
                    .dropDuplicates(["url"])

# --- 6. Écriture MySQL ---
def write_to_mysql(batch_df, batch_id):
    try:
        count = batch_df.count()
        if count > 0:
            print(f"\n{'='*70}")
            print(f"📦 [MAROCANNONCES - Batch {batch_id}] Traitement de {count} annonces...")
            
            import mysql.connector
            conn = mysql.connector.connect(
                host="localhost",
                port=3307,
                user="user",
                password="password",
                database="avito_db"
            )
            cursor = conn.cursor()
            
            urls_in_batch = [row['url'] for row in batch_df.select('url').distinct().collect()]
            
            existing_urls = set()
            if urls_in_batch:
                placeholders = ','.join(['%s'] * len(urls_in_batch))
                cursor.execute(f"SELECT url FROM annonces WHERE url IN ({placeholders})", urls_in_batch)
                existing_urls = set(row[0] for row in cursor.fetchall())
            
            cursor.close()
            conn.close()
            
            new_annonces_df = batch_df.filter(~col('url').isin(existing_urls))
            new_count = new_annonces_df.count()
            
            if new_count > 0:
                new_annonces_df.write \
                    .format("jdbc") \
                    .option("url", "jdbc:mysql://localhost:3307/avito_db") \
                    .option("dbtable", "annonces") \
                    .option("user", "user") \
                    .option("password", "password") \
                    .option("driver", "com.mysql.cj.jdbc.Driver") \
                    .mode("append") \
                    .save()
                print(f"✅ [MAROCANNONCES] {new_count} nouvelles annonces insérées")
            else:
                print(f"ℹ️  [MAROCANNONCES] Uniquement des doublons dans ce batch")
            
            print(f"{'='*70}\n")
            
    except Exception as e:
        print(f"❌ [MAROCANNONCES] Erreur Batch {batch_id}: {e}")

# --- 7. Lancement ---
query = df_clean.writeStream \
    .foreachBatch(write_to_mysql) \
    .outputMode("append") \
    .trigger(processingTime='10 seconds') \
    .start()

try:
    query.awaitTermination()
except KeyboardInterrupt:
    query.stop()
    if producer_process: producer_process.terminate()
    spark.stop()