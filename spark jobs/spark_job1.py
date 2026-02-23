import sys
import os
import subprocess
import threading
import time


if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, LongType


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
print("🎯 SPARK JOB AVITO - DÉMARRAGE")
print("="*70)


producer_process = start_producer("producers/producer1.py")

if producer_process:
    print(f"✅ Producer1 (Avito) lancé - PID: {producer_process.pid}")
else:
    print("⚠️  Producer1 n'a pas démarré")
    sys.exit(1)

print("\n⏳ Attente de 10 secondes pour initialisation...\n")
time.sleep(10)


print("="*70)
print("⚙️  INITIALISATION DE SPARK STREAMING (AVITO)")
print("="*70)

spark = SparkSession.builder \
    .appName("AvitoAdsProcessor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.mysql:mysql-connector-j:8.2.0") \
    .config("spark.sql.streaming.checkpointLocation", "./checkpoint_avito") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")


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
    StructField("timestamp_scraped", LongType())
])


print("\n📡 Connexion à Kafka (Topic: avito_listings)...")
df_kafka = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "avito_listings") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()


df_parsed = df_kafka.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")


def write_to_mysql(batch_df, batch_id):
    """Fonction avec filtrage des doublons avant insertion"""
    try:
        count = batch_df.count()
        if count > 0:
            print(f"\n{'='*70}")
            print(f"📦 [AVITO - Batch {batch_id}] Traitement de {count} annonces...")
            
            
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
            
            if urls_in_batch:
                
                placeholders = ','.join(['%s'] * len(urls_in_batch))
                cursor.execute(f"SELECT url FROM annonces WHERE url IN ({placeholders})", urls_in_batch)
                existing_urls = set(row[0] for row in cursor.fetchall())
            else:
                existing_urls = set()
            
            cursor.close()
            conn.close()
            
            
            new_annonces_df = batch_df.filter(~col('url').isin(existing_urls))
            
            new_count = new_annonces_df.count()
            duplicate_count = count - new_count
            
            print(f"   └─ Nouvelles: {new_count} | Doublons ignorés: {duplicate_count}")
            
            if new_count > 0:
                
                category_counts = new_annonces_df.groupBy("category").count().collect()
                for row in category_counts:
                    print(f"   └─ {row['category']}: {row['count']} annonces")
                
                
                print("\n📋 Aperçu (Avito):")
                new_annonces_df.select("category", "titre", "prix", "localisation").show(5, truncate=False)
                
                
                new_annonces_df.write \
                    .format("jdbc") \
                    .option("url", "jdbc:mysql://localhost:3307/avito_db") \
                    .option("dbtable", "annonces") \
                    .option("user", "user") \
                    .option("password", "password") \
                    .option("driver", "com.mysql.cj.jdbc.Driver") \
                    .mode("append") \
                    .save()
                
                print(f"✅ [AVITO - Batch {batch_id}] {new_count} nouvelles annonces insérées")
            else:
                print(f"ℹ️  [AVITO - Batch {batch_id}] Aucune nouvelle annonce")
            
            print(f"{'='*70}\n")
            
    except Exception as e:
        print(f"❌ [AVITO - Batch {batch_id}] Erreur: {e}")


print("\n" + "="*70)
print("🚀 SPARK STREAMING AVITO DÉMARRÉ !")
print("="*70)
print("\n📊 Catégories surveillées:")
print("   - Voitures d'occasion")
print("   - Immobilier")
print("   - Multimédia")
print("\n⏸️  Appuyez sur Ctrl+C pour arrêter...\n")

query = df_parsed.writeStream \
    .foreachBatch(write_to_mysql) \
    .outputMode("append") \
    .trigger(processingTime='10 seconds') \
    .start()


try:
    query.awaitTermination()
except KeyboardInterrupt:
    print("\n\n🛑 Arrêt demandé...")
    
    query.stop()
    print("✓ Spark Streaming arrêté")
    
    if producer_process and producer_process.poll() is None:
        producer_process.terminate()
        producer_process.wait(timeout=5)
        print("✓ Producer1 (Avito) arrêté")
    
    spark.stop()
    print("✓ Spark Session fermée")
    print("\n👋 Arrêt propre effectué.")