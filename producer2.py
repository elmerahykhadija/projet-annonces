import sys
import os

# ✅ CORRECTION : Forcer l'encodage UTF-8 sur Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import requests
import json
import time
import re
from datetime import datetime, timedelta
from kafka import KafkaProducer
from bs4 import BeautifulSoup

class MarocAnnoncesProducer:
    def __init__(self, bootstrap_servers=['localhost:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.topic = 'annonces-raw'
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.urls = {
            'Auto-Moto': 'https://www.marocannonces.com/categorie/15/Auto-Moto.html?bloc=1',
            'Immobilier': 'https://www.marocannonces.com/categorie/16/Vente-immobilier.html?bloc=1',
            'Multimedia': 'https://www.marocannonces.com/categorie/306/Multim%C3%A9dia.html?bloc=1'
        }
        
        # Cache pour stocker les annonces déjà envoyées
        self.sent_annonces = set()
    
    def generate_annonce_id(self, annonce):
        """Génère un ID unique pour une annonce basé sur son URL"""
        return annonce['url']
    
    def parse_date(self, date_text):
        """Parse la date et retourne True si c'est dans les 72 dernières heures (3 jours)"""
        try:
            # MODIFICATION: Scraper les 3 derniers jours (72h)
            scrape_days = 3
            
            # Cas 1: Aujourd'hui
            if "Aujourd'hui" in date_text or "cnt-today" in date_text:
                return True
            
            # Cas 2: Hier (si présent)
            if "Hier" in date_text or "Yesterday" in date_text:
                return True
            
            # Cas 3: Date exacte (ex: "10 Déc 2024")
            date_match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_text)
            if date_match:
                day = int(date_match.group(1))
                month_str = date_match.group(2)
                year = int(date_match.group(3))
                
                months = {
                    'Jan': 1, 'Fév': 2, 'Mar': 3, 'Avr': 4, 'Mai': 5, 'Juin': 6,
                    'Juil': 7, 'Aoû': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Déc': 12
                }
                month = months.get(month_str, 1)
                
                annonce_date = datetime(year, month, day)
                date_limite = datetime.now() - timedelta(days=scrape_days)
                
                return annonce_date >= date_limite
            
            return False
        except Exception as e:
            print(f"Erreur parsing date: {e}")
            return False
    
    def extract_annonces(self, html_content, category):
        """Extrait les annonces du HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        annonces = []
        
        # Trouver toutes les annonces dans la liste
        items = soup.select('ul.cars-list > li')
        
        for item in items:
            # Ignorer les publicités
            if 'adslistingpos' in item.get('class', []):
                continue
            
            try:
                # Extraire la date
                date_elem = item.select_one('.date')
                if not date_elem:
                    continue
                
                date_text = date_elem.get_text(strip=True)
                
                # Filtrer par date (2 derniers jours)
                if not self.parse_date(str(date_elem)):
                    continue
                
                # Extraire le lien et le titre
                link = item.select_one('a')
                if not link:
                    continue
                
                titre_elem = link.select_one('h3')
                titre = titre_elem.get_text(strip=True) if titre_elem else 'N/A'
                url = link.get('href', '')
                
                # Construire l'URL complète
                if url and not url.startswith('http'):
                    url = f"https://www.marocannonces.com/{url}"
                
                # Extraire le prix
                prix_elem = item.select_one('.price')
                prix = prix_elem.get_text(strip=True) if prix_elem else 'N/A'
                
                # Extraire la localisation
                location_elem = item.select_one('.location')
                localisation = location_elem.get_text(strip=True) if location_elem else 'N/A'
                
                # Extraire la sous-catégorie
                views_elem = item.select_one('.views')
                sous_categorie = views_elem.get_text(strip=True) if views_elem else category
                
                # Extraire l'image
                img_elem = item.select_one('img.lazy')
                image_url = img_elem.get('data-original', '') if img_elem else 'N/A'
                if image_url and not image_url.startswith('http'):
                    if not 'icon-no-photo' in image_url:
                        image_url = f"https://www.marocannonces.com/{image_url}"
                    else:
                        image_url = 'N/A'
                
                # Créer l'object annonce
                annonce = {
                    'source': 'marocannonces',
                    'category': category,
                    'sous_categorie': sous_categorie,
                    'titre': titre,
                    'prix': prix,
                    'localisation': localisation,
                    'url': url,
                    'image_url': image_url,
                    'date_text': date_text,
                    'timestamp': time.time()
                }
                
                annonces.append(annonce)
                
            except Exception as e:
                print(f"Erreur extraction annonce: {e}")
                continue
        
        return annonces
    
    def scrape_category(self, url, category):
        """Scrape une catégorie"""
        try:
            print(f"\n{'='*60}")
            print(f"Scraping: {category}")
            print(f"URL: {url}")
            print(f"{'='*60}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            annonces = self.extract_annonces(response.text, category)
            
            # Filtrer les annonces déjà envoyées
            nouvelles_annonces = []
            for annonce in annonces:
                annonce_id = self.generate_annonce_id(annonce)
                if annonce_id not in self.sent_annonces:
                    nouvelles_annonces.append(annonce)
                    self.sent_annonces.add(annonce_id)
            
            print(f"Trouvé {len(annonces)} annonces au total")
            print(f"Nouvelles annonces: {len(nouvelles_annonces)}")
            
            # Envoyer uniquement les nouvelles annonces vers Kafka
            if nouvelles_annonces:
                for annonce in nouvelles_annonces:
                    self.send_to_kafka(annonce)
                    print(f"✓ NOUVELLE: {annonce['titre'][:50]}... - {annonce['prix']}")
            else:
                print(f"ℹ️  Aucune nouvelle annonce")
            
            return len(nouvelles_annonces)
            
        except Exception as e:
            print(f"Erreur scraping {category}: {e}")
            return 0
    
    def send_to_kafka(self, data):
        """Envoie les données vers Kafka"""
        try:
            self.producer.send(self.topic, value=data)
            self.producer.flush()
        except Exception as e:
            print(f"Erreur envoi Kafka: {e}")
    
    def cleanup_old_cache(self):
        """Nettoie le cache des annonces trop anciennes (> 3 jours)"""
        # Pour éviter que le cache devienne trop gros, 
        # on peut le vider périodiquement ou limiter sa taille
        if len(self.sent_annonces) > 10000:
            print("⚠️  Cache trop volumineux, nettoyage...")
            # Garder seulement les 5000 dernières
            self.sent_annonces = set(list(self.sent_annonces)[-5000:])
            print(f"✓ Cache réduit à {len(self.sent_annonces)} entrées")
    
    def run_continuous(self, interval_seconds=60):  # Scrape toutes les minutes
        """Exécute le scraping en continu"""
        print(f"🚀 Démarrage du scraping 24/7 (intervalle: {interval_seconds}s)")
        
        while True:
            try:
                print(f"\n{'='*60}")
                print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'='*60}")
                
                for category, url in self.urls.items():
                    self.scrape_category(url, category)
                
                # Nettoyer le cache périodiquement
                self.cleanup_old_cache()
                
                print(f"\n✅ Cycle terminé. Prochaine exécution dans {interval_seconds}s...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("\n🛑 Arrêt demandé")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")
                print(f"⏳ Retry dans 30s...")
                time.sleep(30)
    
    def close(self):
        """Ferme les connexions"""
        self.producer.close()
        print(f"Producer fermé - {len(self.sent_annonces)} annonces en cache")

if __name__ == "__main__":
    producer = MarocAnnoncesProducer()
    try:
        # Exécuter en continu toutes les 30 secondes
        producer.run_continuous(interval_seconds=30)
    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur")
    finally:
        producer.close()
        print("Producer fermé")
