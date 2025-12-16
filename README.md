# 🛒 Marketplace Aggregator - Projet Annonces

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Kafka](https://img.shields.io/badge/Apache%20Kafka-Latest-black.svg)
![Spark](https://img.shields.io/badge/Apache%20Spark-3.5.0-orange.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)

## 📋 Description

**Marketplace Aggregator** est une application de scraping et d'agrégation d'annonces en temps réel provenant de plusieurs plateformes marocaines (Avito, MarocAnnonces). Le système collecte, traite via Apache Spark Streaming et affiche les données dans une interface web moderne avec dashboard analytique.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SOURCES DE DONNÉES                           │
│  ┌──────────────┐              ┌──────────────┐                 │
│  │   Avito.ma   │              │MarocAnnonces │                 │
│  │   (GraphQL)  │              │    (HTML)    │                 │
│  └──────┬───────┘              └──────┬───────┘                 │
└─────────┼──────────────────────────────┼────────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              COUCHE D'EXTRACTION (Scraping)                      │
│  ┌──────────────┐              ┌──────────────┐                 │
│  │ producer1.py │              │producer2.py  │                 │
│  │ Scrape Avito │              │Scrape MA     │                 │
│  │ (60s cycle)  │              │ (30s cycle)  │                 │
│  └──────┬───────┘              └──────┬───────┘                 │
└─────────┼──────────────────────────────┼────────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MESSAGE BROKER (Kafka)                          │
│  ┌────────────────────┐    ┌─────────────────────┐             │
│  │ Topic: avito_listings │    │Topic: annonces-raw│             │
│  │    (Producer1)      │    │    (Producer2)     │             │
│  └─────────┬──────────┘    └──────────┬─────────┘             │
└────────────┼─────────────────────────┼────────────────────────┘
             │                         │
             ▼                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           STREAM PROCESSING (Apache Spark)                       │
│  ┌──────────────┐              ┌──────────────┐                 │
│  │spark_job1.py │              │spark_job2.py │                 │
│  │Process Avito │              │  Process MA  │                 │
│  │(10s batch)   │              │ (10s batch)  │                 │
│  └──────┬───────┘              └──────┬───────┘                 │
└─────────┼──────────────────────────────┼────────────────────────┘
          │                              │
          └──────────────┬───────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 STOCKAGE (MySQL 8.0)                             │
│         Database: avito_db | Port: 3307                          │
│              Table: annonces                                     │
│      Deduplication basée sur URL                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              APPLICATION LAYER (Streamlit)                       │
│  ┌──────────────┐              ┌──────────────┐                 │
│  │   app.py     │              │dashboard.py  │                 │
│  │ (Main UI)    │              │ (Analytics)  │                 │
│  │  Cache: 30s  │              │Auto-refresh:5s│                 │
│  └──────┬───────┘              └──────┬───────┘                 │
└─────────┼──────────────────────────────┼────────────────────────┘
          │                              │
          └──────────────┬───────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   UTILISATEURS FINAUX                            │
│                    (Web Browser)                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Technologies Utilisées

- **Backend**
  - Python 3.9+
  - Apache Kafka (Message Broker)
  - Apache Spark 3.5.0 (Stream Processing)
  - MySQL 8.0 (Base de données - Port 3307)
  - Requests + BeautifulSoup4 (Scraping)

- **Frontend**
  - Streamlit (Interface web)
  - Plotly (Graphiques interactifs)
  - Pandas (Manipulation de données)

## 📦 Prérequis

- Python 3.9 ou supérieur
- Java 11+ (pour Spark)
- MySQL Server (port 3307)
- Apache Kafka + Zookeeper
- Apache Spark 3.5.0
- Connexion Internet (pour le scraping)

## ⚙️ Installation

### 1. Cloner le projet

```bash
git clone https://github.com/votre-username/projet-annonces.git
cd projet-annonces
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
venv\Scripts\activate  # Sur Windows
# source venv/bin/activate  # Sur Linux/Mac
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Contenu de `requirements.txt` :**
```txt
streamlit==1.28.0
pandas==2.1.0
mysql-connector-python==8.1.0
kafka-python==2.0.2
requests==2.31.0
beautifulsoup4==4.12.2
plotly==5.17.0
pyspark==3.5.0
```

### 4. Configuration de la base de données

```sql
CREATE DATABASE avito_db;

USE avito_db;

CREATE TABLE annonces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(50),
    category VARCHAR(100),
    sous_categorie VARCHAR(100),
    titre TEXT,
    prix VARCHAR(50),
    localisation VARCHAR(100),
    url TEXT UNIQUE,
    image_url TEXT,
    date_text VARCHAR(100),
    timestamp_scraped BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source (source),
    INDEX idx_category (category),
    INDEX idx_url (url(255)),
    INDEX idx_timestamp (timestamp_scraped)
);
```

### 5. Démarrer Kafka et Zookeeper

**Sous Windows :**
```bash
# Terminal 1 - Zookeeper
cd C:\kafka
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

# Terminal 2 - Kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

### 6. Créer les topics Kafka

```bash
# Topic pour Avito
.\bin\windows\kafka-topics.bat --create --topic avito_listings --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Topic pour MarocAnnonces
.\bin\windows\kafka-topics.bat --create --topic annonces-raw --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

## 🎮 Utilisation

### Architecture de Démarrage

**⚠️ IMPORTANT : Les Spark Jobs lancent automatiquement les Producers !**

Vous n'avez besoin que de **2 terminaux Spark + 2 terminaux Streamlit**.

### 1. Lancer Spark Job 1 (Avito) - Lance automatiquement producer1.py

```bash
python spark_job1.py
```
Ce script va :
- ✅ Démarrer `producer1.py` (scraping Avito toutes les 60s)
- ✅ Consommer le topic `avito_listings`
- ✅ Traiter les données avec Spark Streaming
- ✅ Insérer dans MySQL avec deduplication

### 2. Lancer Spark Job 2 (MarocAnnonces) - Lance automatiquement producer2.py

```bash
python spark_job2.py
```
Ce script va :
- ✅ Démarrer `producer2.py` (scraping MarocAnnonces toutes les 30s)
- ✅ Consommer le topic `annonces-raw`
- ✅ Traiter les données avec Spark Streaming
- ✅ Insérer dans MySQL avec deduplication

### 3. Lancer l'application Streamlit principale

```bash
streamlit run app.py
```

Interface accessible sur : `http://localhost:8501`

### 4. Lancer le Dashboard Analytics

```bash
streamlit run dashboard.py
```

Dashboard accessible sur : `http://localhost:8502`

## 📁 Structure du Projet

```
projet-annonces/
│
├── producer1.py           # Producer Kafka pour Avito (API GraphQL)
├── producer2.py           # Producer Kafka pour MarocAnnonces (HTML)
├── spark_job1.py          # Spark Streaming Job pour Avito (lance producer1)
├── spark_job2.py          # Spark Streaming Job pour MarocAnnonces (lance producer2)
├── app.py                 # Application principale Streamlit
├── dashboard.py           # Dashboard analytique avec auto-refresh (5s)
├── requirements.txt       # Dépendances Python
├── checkpoint_avito/      # Checkpoints Spark Job 1 (généré auto)
├── checkpoint_marocannonces/  # Checkpoints Spark Job 2 (généré auto)
└── README.md             # Documentation
```

## ✨ Fonctionnalités

### Producer 1 (Avito)
- ✅ Scraping via API GraphQL officielle
- ✅ Cycle : 60 secondes
- ✅ Gestion du cache (évite doublons en mémoire)
- ✅ Extraction :
  - Titre, Prix, Catégorie
  - Localisation (Ville)
  - Images
  - URL unique

### Producer 2 (MarocAnnonces)
- ✅ Scraping HTML avec BeautifulSoup4
- ✅ Cycle : 30 secondes
- ✅ Filtre : **Dernières 72 heures** (3 jours)
- ✅ Catégories : Auto-Moto, Immobilier, Multimédia
- ✅ Détection des doublons avant envoi

### Spark Jobs
- ✅ **Lancement automatique** des producers
- ✅ Stream Processing (micro-batching : 10 secondes)
- ✅ **Deduplication MySQL** avant insertion (basée sur URL)
- ✅ Compteurs par catégorie
- ✅ Gestion des erreurs et logging

### Application Principale (app.py)
- ✅ Affichage en **grille 3 colonnes**
- ✅ **Filtres avancés** :
  - 📂 Catégorie
  - 📍 Ville
  - 🌐 Source (Avito / MarocAnnonces)
  - 💰 **Budget maximum (saisie manuelle)**
  - 🔍 Recherche par mot-clé
- ✅ Cache intelligent (TTL 30s)
- ✅ Design moderne avec CSS personnalisé
- ✅ Badges colorés par source

### Dashboard Analytics (dashboard.py)
- ✅ **Auto-refresh : 5 secondes**
- ✅ **KPIs en temps réel** :
  - Total d'annonces
  - Prix moyen
  - Nombre de villes
  - Dernière mise à jour (HH:MM:SS)
- ✅ **Graphiques interactifs** :
  - 🥧 Répartition par source (Pie Chart)
  - 📊 Top catégories (Bar Chart)
  - 📦 Distribution des prix (Boxplot)
- ✅ Tableau des 50 dernières annonces

## 🔧 Configuration

### Modifier les intervalles de scraping

**producer1.py (Avito) :**
```python
# Ligne 170
time.sleep(60)  # Modifier l'intervalle (en secondes)
```

**producer2.py (MarocAnnonces) :**
```python
# Ligne 199
producer.run_continuous(interval_seconds=30)  # Modifier ici
```

### Modifier la période de scraping (72h)

**producer2.py :**
```python
# Ligne 54
scrape_days = 3  # Changer le nombre de jours
```

### Modifier l'auto-refresh du dashboard

**dashboard.py :**
```python
# Ligne 33
@st.cache_data(ttl=5)  # Modifier le TTL du cache

# Ligne 108
time.sleep(5)  # Modifier l'intervalle de refresh
```

### Modifier le batch Spark

**spark_job1.py et spark_job2.py :**
```python
# Dernière ligne avant .start()
.trigger(processingTime='10 seconds')  # Modifier ici
```

## 📊 Flux de Données

```
1. Producer scrape les sites web (60s pour Avito, 30s pour MA)
2. Envoi des messages JSON vers Kafka
3. Spark Streaming consomme les topics
4. Traitement : parsing + deduplication
5. Insertion dans MySQL (table annonces)
6. Streamlit lit MySQL et affiche les données
```

## 🐛 Résolution de Problèmes

### Erreur : "No module named 'pyspark'"
```bash
pip install pyspark==3.5.0
```

### Erreur : Spark ne trouve pas Java
```bash
# Installer Java 11+
# Windows : Télécharger depuis Oracle
# Vérifier :
java -version
```

### Erreur : Connexion MySQL refusée
```bash
# Vérifier que MySQL tourne sur le port 3307
mysql -u user -p -P 3307 -h localhost
```

### Erreur : Kafka n'est pas accessible
```bash
# Vérifier Zookeeper et Kafka
# Tester la connexion
telnet localhost 9092
```

### Les Spark Jobs ne démarrent pas les producers
Vérifiez que `producer1.py` et `producer2.py` sont dans le même dossier que les spark_jobs.

### Les annonces ne s'affichent pas dans Streamlit
1. Vérifiez que les Spark Jobs tournent
2. Vérifiez que les données arrivent dans MySQL :
```sql
SELECT COUNT(*), source FROM annonces GROUP BY source;
```

## 📈 Monitoring

### Vérifier les topics Kafka
```bash
# Liste des topics
.\bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092

# Messages dans un topic
.\bin\windows\kafka-console-consumer.bat --bootstrap-server localhost:9092 --topic avito_listings --from-beginning
```

### Vérifier MySQL
```sql
-- Nombre total d'annonces
SELECT COUNT(*) FROM annonces;

-- Par source
SELECT source, COUNT(*) FROM annonces GROUP BY source;

-- Dernières annonces
SELECT titre, prix, source, FROM_UNIXTIME(timestamp_scraped) 
FROM annonces 
ORDER BY timestamp_scraped DESC 
LIMIT 10;
```

## 🤝 Contributions

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Committez vos changements (`git commit -m 'Ajout fonctionnalité X'`)
4. Pushez vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT.

## 👤 Auteur

**Elmer**
- Projet : Marketplace Aggregator
- Date : Décembre 2024

## 📧 Contact

Pour toute question :
- Email: votre.email@example.com
- GitHub: [@votre-username](https://github.com/votre-username)

---

## 🎯 Spécifications Techniques

### Infrastructure
- **OS**: Windows 10/11
- **Python**: 3.9+
- **Kafka**: 3.5.0
- **Spark**: 3.5.0
- **MySQL**: 8.0 (Port 3307)

### Performance
- **Producer1 (Avito)**: ~50-100 annonces/minute
- **Producer2 (MA)**: ~20-50 annonces/minute
- **Spark Streaming**: Batch 10 secondes
- **Latence Kafka**: < 100ms
- **Deduplication**: Basée sur URL (UNIQUE constraint)

### Volumes
- **Annonces totales**: ~500-1000/jour
- **Taille DB**: ~50MB
- **Throughput Kafka**: ~5-10 messages/seconde

---

⭐ **Si ce projet vous a été utile, n'oubliez pas de mettre une étoile !**
