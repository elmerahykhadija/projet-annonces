import sys
import os


if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from kafka.admin import KafkaAdminClient, NewTopic
import requests
import json
import time
from datetime import datetime

# --- CONFIGURATION KAFKA ---
try:
    admin_client = KafkaAdminClient(
        bootstrap_servers=['localhost:9092'],
        client_id='avito_producer'
    )
    
    topic_list = [NewTopic(name="avito_listings", num_partitions=1, replication_factor=1)]
    
    try:
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        print("Topic 'avito_listings' cree avec succes")
    except Exception as e:
        print(f"INFO: Topic existe deja : {e}")
    
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("Connexion Kafka reussie")
    
except NoBrokersAvailable:
    print("ERREUR: Impossible de se connecter a Kafka")
    sys.exit(1)
except Exception as e:
    print(f"ERREUR Kafka : {e}")
    sys.exit(1)

TOPIC_NAME = 'avito_listings'

# --- CONFIGURATION SCRAPING ---
URL = "https://gateway.avito.ma/graphql"
DELAY_SECONDS = 60

# Headers exacts d'Avito
headers = {
    'accept': 'application/graphql-response+json,application/json;q=0.9',
    'accept-language': 'fr',
    'content-type': 'application/json',
    'origin': 'https://www.avito.ma',
    'referer': 'https://www.avito.ma/',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'user-session-id': 'undefined',
    'visitorid': 'undefined'
}

# Cache pour éviter doublons
sent_urls = set()

def scrape_avito():
    """Scrape les annonces Avito avec la vraie API"""
    
    # La vraie requête GraphQL d'Avito
    query = """
    query getListingSections {
      getListingSections {
        sections {
          id
          listingUrl
          title
          order
          ads {
            adId
            listId
            category {
              id
              name
              __typename
            }
            type {
              key
              name
              __typename
            }
            title
            description
            price {
              withCurrency
              withoutCurrency
              __typename
            }
            oldPrice {
              withCurrency
              withoutCurrency
              __typename
            }
            discount
            media {
              defaultImage {
                paths {
                  standard
                  __typename
                }
                __typename
              }
              __typename
            }
            seller {
              ... on PrivateProfile {
                name
                __typename
              }
              ... on StoreProfile {
                name
                isVerifiedSeller
                __typename
              }
              __typename
            }
            location {
              city {
                id
                name
                __typename
              }
              area {
                id
                name
                __typename
              }
              address
              __typename
            }
            listTime
            isHighlighted
            isUrgent
            isHotDeal
            __typename
          }
          __typename
        }
        __typename
      }
    }
    """
    
    payload = {
        "operationName": "getListingSections",
        "variables": {},
        "query": query
    }
    
    try:
        response = requests.post(URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"ERREUR HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return 0
        
        data = response.json()
        
        # Parcourir les sections
        sections = data.get('data', {}).get('getListingSections', {}).get('sections', [])
        
        count = 0
        for section in sections:
            section_title = section.get('title', 'Unknown')
            ads = section.get('ads', [])
            
            print(f"\n--- Section: {section_title} ({len(ads)} annonces) ---")
            
            for ad in ads:
                try:
                    # Construire l'URL de l'annonce
                    ad_id = ad.get('adId', '')
                    list_id = ad.get('listId', '')
                    
                    if not ad_id:
                        continue
                    
                    annonce_url = f"https://www.avito.ma/fr/{list_id}/{ad_id}"
                    
                    # Éviter doublons
                    if annonce_url in sent_urls:
                        continue
                    
                    sent_urls.add(annonce_url)
                    
                    # Extraire les données
                    titre = ad.get('title', 'N/A')
                    category = ad.get('category', {}).get('name', 'N/A')
                    
                    price_obj = ad.get('price', {})
                    prix = price_obj.get('withCurrency', 'N/A') if price_obj else 'N/A'
                    
                    location = ad.get('location', {})
                    city = location.get('city', {}).get('name', 'N/A') if location else 'N/A'
                    
                    media = ad.get('media', {})
                    default_image = media.get('defaultImage', {}) if media else {}
                    image_url = 'N/A'
                    if default_image:
                        paths = default_image.get('paths', {})
                        image_url = paths.get('standard', 'N/A')
                    
                    list_time = ad.get('listTime', datetime.now().isoformat())
                    
                    # Créer l'objet annonce
                    annonce_data = {
                        'source': 'avito',
                        'category': category,
                        'sous_categorie': section_title,
                        'titre': titre,
                        'prix': prix,
                        'localisation': city,
                        'url': annonce_url,
                        'image_url': image_url,
                        'date_text': list_time,
                        'timestamp_scraped': int(time.time())
                    }
                    
                    # Envoyer vers Kafka
                    producer.send(TOPIC_NAME, value=annonce_data)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {titre[:60]}")
                    count += 1
                    
                except Exception as e:
                    print(f"Erreur extraction annonce: {e}")
                    continue
        
        return count
        
    except Exception as e:
        print(f"ERREUR scraping: {e}")
        import traceback
        traceback.print_exc()
        return 0

# --- SCRAPING CONTINU ---
print(f"\n{'='*60}")
print("Demarrage du scraping Avito 24/7 (API GraphQL)")
print(f"{'='*60}\n")

try:
    cycle_count = 0
    
    while True:
        cycle_count += 1
        print(f"\n[CYCLE #{cycle_count}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        count = scrape_avito()
        print(f"\n>>> Total: {count} annonces ce cycle")
        
        # Nettoyer le cache périodiquement
        if len(sent_urls) > 2000:
            print("Nettoyage du cache...")
            sent_urls.clear()
        
        print(f"\nProchaine execution dans {DELAY_SECONDS}s...")
        time.sleep(DELAY_SECONDS)
        
except KeyboardInterrupt:
    print("\n\nArret demande")
    producer.close()

    print("Producer ferme proprement")
