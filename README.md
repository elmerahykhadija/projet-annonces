# 🛒 Marketplace - Projet Annonces

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Kafka](https://img.shields.io/badge/Apache%20Kafka-Latest-black.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)

## 📋 Description

**Marketplace Aggregator** est une application de scraping et d'agrégation d'annonces en temps réel provenant de plusieurs plateformes marocaines (Avito, MarocAnnonces). Le système collecte, traite et affiche les données dans une interface web moderne avec dashboard analytique.

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐
│   Avito     │────▶│  Producer1  │
└─────────────┘     └──────┬──────┘
                           │
┌─────────────┐     ┌──────▼──────┐     ┌──────────┐     ┌──────────┐
│MarocAnnonces│────▶│  Producer2  │────▶│  Kafka   │────▶│ Consumer │────▶│  MySQL   │
└─────────────┘     └─────────────┘     └──────────┘     └──────────┘     └────┬─────┘
                                                                                 │
                                                          ┌──────────────────────┘
                                                          │
                                                          ▼
                                               ┌────────────────────┐
                                               │   Streamlit App    │
                                               │  (app.py + dash)   │
                                               └────────────────────┘
```

## 🚀 Technologies Utilisées

- **Backend**
  - Python 3.9+
  - Apache Kafka (Streaming)
  - MySQL 8.0 (Base de données)
  - Requests + BeautifulSoup4 (Scraping)

- **Frontend**
  - Streamlit (Interface web)
  - Plotly (Graphiques interactifs)
  - Pandas (Manipulation de données)

## 📦 Prérequis

- Python 3.9 ou supérieur
- MySQL Server (port 3307)
- Apache Kafka + Zookeeper
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
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
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
```

### 4. Configuration de la base de données

```sql
CREATE DATABASE avito_db;

USE avito_db;

CREATE TABLE annonces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(50),
    category VARCHAR(100),
    titre TEXT,
    prix VARCHAR(50),
    localisation VARCHAR(100),
    url TEXT,
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_source (source),
    INDEX idx_category (category),
    INDEX idx_created_at (created_at)
);
```

### 5. Démarrer Kafka et Zookeeper

**Sous Windows :**
```bash
# Terminal 1 - Zookeeper
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

# Terminal 2 - Kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

**Sous Linux/Mac :**
```bash
# Terminal 1 - Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties

# Terminal 2 - Kafka
bin/kafka-server-start.sh config/server.properties
```

### 6. Créer le topic Kafka

```bash
# Windows
.\bin\windows\kafka-topics.bat --create --topic annonces-raw --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Linux/Mac
bin/kafka-topics.sh --create --topic annonces-raw --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

## 🎮 Utilisation

### 1. Démarrer le Consumer (Base de données)

```bash
python consumer.py
```

### 2. Lancer les Producers (Scraping)

**Terminal 1 - Producer Avito :**
```bash
python producer.py
```

**Terminal 2 - Producer MarocAnnonces :**
```bash
python producer2.py
```

### 3. Lancer l'application Streamlit

**Interface principale :**
```bash
streamlit run app.py
```

**Dashboard Analytics :**
```bash
streamlit run dashboard.py
```

## 📁 Structure du Projet

```
projet-annonces/
│
├── app.py                 # Application principale Streamlit
├── dashboard.py           # Dashboard analytique avec auto-refresh (5s)
├── producer.py            # Producer Kafka pour Avito
├── producer2.py           # Producer Kafka pour MarocAnnonces
├── consumer.py            # Consumer Kafka → MySQL
├── requirements.txt       # Dépendances Python
└── README.md             # Documentation
```

## ✨ Fonctionnalités

### Application Principale (app.py)
- ✅ Affichage en grille de 3 colonnes
- ✅ Filtres avancés :
  - Catégorie
  - Ville
  - Source (Avito / MarocAnnonces)
  - Budget maximum
  - Recherche par mot-clé
- ✅ Cache intelligent (TTL 30s)
- ✅ Design responsive avec CSS personnalisé

### Dashboard Analytics (dashboard.py)
- ✅ Auto-refresh toutes les 5 secondes
- ✅ KPIs en temps réel :
  - Total d'annonces
  - Prix moyen
  - Nombre de villes
  - Dernière mise à jour
- ✅ Graphiques interactifs :
  - Répartition par source (Pie Chart)
  - Top catégories (Bar Chart)
  - Distribution des prix (Boxplot)
- ✅ Tableau des données brutes

### Producers
- ✅ Scraping automatique toutes les 30 secondes
- ✅ Filtrage des annonces des 72 dernières heures
- ✅ Détection des doublons
- ✅ Gestion des erreurs et retry automatique

### Consumer
- ✅ Insertion en base de données en temps réel
- ✅ Détection des doublons (basée sur l'URL)
- ✅ Transactions MySQL optimisées

## 🔧 Configuration

### Modifier les paramètres de scraping

**producer.py / producer2.py :**
```python
# Intervalle de scraping (en secondes)
producer.run_continuous(interval_seconds=30)

# Période de scraping (en jours)
scrape_days = 3  # 72 heures
```

### Modifier l'auto-refresh du dashboard

**dashboard.py :**
```python
@st.cache_data(ttl=5)  # Modifier le TTL (en secondes)

# Ligne 108
time.sleep(5)  # Modifier l'intervalle de refresh
```

## 📊 Exemples de Données

**Format des annonces collectées :**
```json
{
  "source": "avito",
  "category": "Auto-Moto",
  "titre": "Dacia Logan 2015 - Essence",
  "prix": "65 000 DH",
  "localisation": "Casablanca",
  "url": "https://www.avito.ma/...",
  "image_url": "https://...",
  "created_at": "2024-12-11 21:43:52"
}
```

## 🐛 Résolution de Problèmes

### Erreur : "No module named 'streamlit'"
```bash
pip install streamlit
```

### Erreur : Connexion MySQL refusée
Vérifiez que MySQL tourne sur le port 3307 :
```bash
mysql -u user -p -P 3307 -h localhost
```

### Erreur : Kafka n'est pas accessible
Assurez-vous que Zookeeper et Kafka sont démarrés :
```bash
# Tester la connexion
telnet localhost 9092
```

### Les annonces ne s'affichent pas
1. Vérifiez que les producers tournent
2. Vérifiez que le consumer insère les données :
```sql
SELECT COUNT(*) FROM annonces;
```

## 🤝 Contributions

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Committez vos changements (`git commit -m 'Ajout fonctionnalité X'`)
4. Pushez vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👤 Auteur

**Elmer**
- Projet : Marketplace Aggregator
- Date : Décembre 2024

## 📧 Contact

Pour toute question ou suggestion :
- Email : votre.email@example.com
- GitHub : [@votre-username](https://github.com/votre-username)

---

⭐ **Si ce projet vous a été utile, n'oubliez pas de mettre une étoile !**