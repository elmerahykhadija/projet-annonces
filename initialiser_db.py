import mysql.connector
import time

def init_db():
    print("Tentative de connexion à MySQL...")
    # On attend un peu que le conteneur soit prêt
    time.sleep(5) 
    
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=3307,        # Port externe défini dans docker-compose
            user="user",
            password="password",
            database="avito_db"
        )
        cursor = conn.cursor()
        
        # Syntaxe MySQL pour créer la table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS annonces (
            id INT AUTO_INCREMENT PRIMARY KEY,
            source VARCHAR(50),
            category VARCHAR(100),
            sous_categorie VARCHAR(100),
            titre TEXT,
            prix VARCHAR(50),
            localisation VARCHAR(100),
            url VARCHAR(768) UNIQUE,
            image_url TEXT,
            date_text VARCHAR(100),
            timestamp_scraped BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        # Note: VARCHAR(768) est utilisé pour l'index UNIQUE car MySQL a une limite sur la taille des clés
        
        cursor.execute(create_table_query)
        conn.commit()
        print("✅ Table 'annonces' créée avec succès dans MySQL (Port 3307)")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Erreur connexion MySQL: {e}")

if __name__ == "__main__":
    init_db()