import streamlit as st
import pandas as pd
import mysql.connector
import re
from datetime import datetime

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Marketplace Finder Pro",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLE CSS AVANCÉ ---
st.markdown("""
<style>
    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Badge Source */
    .source-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        color: white;
        margin-bottom: 8px;
    }
    .avito { background-color: #0069d9; } /* Bleu Avito */
    .marocannonces { background-color: #e85d04; } /* Orange MA */
    
    /* Prix */
    .price-tag {
        font-size: 1.3rem;
        font-weight: 800;
        color: #198754; /* Vert succès */
        margin: 8px 0;
    }
    
    /* Ville et Date */
    .meta-info {
        font-size: 0.85rem;
        color: #6c757d;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    /* Titre Annonce */
    .ad-title {
        font-size: 1.1rem;
        font-weight: 600;
        line-height: 1.4;
        margin-bottom: 5px;
        height: 3em; /* Limite hauteur */
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    
    /* Images */
    div[data-testid="stImage"] img {
        border-radius: 8px;
        object-fit: cover;
        height: 200px !important; /* Hauteur fixe pour uniformité */
    }
    
    /* Bouton Lien */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. FONCTIONS BACKEND ---

def get_db_connection():
    """Crée une connexion optimisée pour la lecture"""
    conn = mysql.connector.connect(
        host="localhost",
        port=3307,
        user="user",
        password="password",
        database="avito_db",
        connection_timeout=5
    )
    conn.start_transaction(readonly=True, isolation_level='READ UNCOMMITTED')
    return conn

def clean_price(price_str):
    if not price_str or pd.isna(price_str): return 0.0
    clean_str = re.sub(r'[^\d]', '', str(price_str))
    try:
        return float(clean_str)
    except:
        return 0.0

@st.cache_data(ttl=30)
def load_data():
    try:
        conn = get_db_connection()
        query = "SELECT * FROM annonces ORDER BY timestamp_scraped DESC LIMIT 2000"
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            df['prix_num'] = df['prix'].apply(clean_price)
            df['localisation'] = df['localisation'].fillna('Autre')
            df['category'] = df['category'].fillna('Divers')
            # Standardisation des sources pour le CSS
            df['source_clean'] = df['source'].astype(str).str.lower().str.replace(' ', '')
        
        return df
    except Exception as e:
        st.error("⚠️ Impossible de se connecter à la base de données.")
        return pd.DataFrame()

# --- 4. INTERFACE UTILISATEUR ---

# Chargement
df = load_data()

# --- SIDEBAR (FILTRES) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3081/3081840.png", width=50)
    st.title("Filtres")
    
    if not df.empty:
        # A. Catégorie
        categories = ["Toutes"] + sorted(df['category'].unique().tolist())
        selected_category = st.selectbox("📂 Catégorie", categories)
        
        # B. Ville
        villes = ["Toutes"] + sorted(df['localisation'].unique().tolist())
        selected_city = st.selectbox("📍 Ville", villes)
        
        # C. Sources
        st.markdown("---")
        st.markdown("**🌐 Plateformes**")
        col_s1, col_s2 = st.columns(2)
        use_avito = col_s1.checkbox("Avito", True)
        use_ma = col_s2.checkbox("MarocAnnonces", True)
        
        selected_sources = []
        if use_avito: selected_sources.append('avito')
        if use_ma: selected_sources.append('marocannonces')

        # D. Budget (MODIFICATION ICI : Saisie manuelle)
        st.markdown("---")
        
        # On calcule le max pour mettre une valeur par défaut cohérente
        max_val_db = int(df['prix_num'].max()) if df['prix_num'].max() > 0 else 1000000
        
        # Champ de saisie numérique (step=100 permet d'augmenter avec les flèches, mais on peut taper)
        budget = st.number_input(
            "💰 Budget Maximum (DH)", 
            min_value=0, 
            value=max_val_db, 
            step=500,
            help="Tapez votre budget maximum ici"
        )

        # E. Recherche
        st.markdown("---")
        search_query = st.text_input("🔍 Recherche mot-clé", placeholder="Ex: iPhone, Clio...")
        
        st.caption(f"v1.3.0 • {len(df)} annonces en base")

# --- LOGIQUE DE FILTRAGE ---
if not df.empty:
    filtered_df = df.copy()
    
    if selected_category != "Toutes":
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    if selected_city != "Toutes":
        filtered_df = filtered_df[filtered_df['localisation'] == selected_city]
    
    filtered_df = filtered_df[filtered_df['source'].isin(selected_sources)]
    filtered_df = filtered_df[filtered_df['prix_num'] <= budget]
    
    if search_query:
        filtered_df = filtered_df[filtered_df['titre'].str.contains(search_query, case=False, na=False)]
else:
    filtered_df = pd.DataFrame()

# --- HEADER PRINCIPAL ---
st.title("🛒 Marketplace Aggregator")
st.markdown("Explorez les meilleures offres regroupées en temps réel.")
st.divider() # Ligne de séparation simple

# --- AFFICHAGE EN GRILLE ---
if not filtered_df.empty:
    
    cols = st.columns(3) # Grille de 3 colonnes
    
    for idx, row in enumerate(filtered_df.itertuples()):
        with cols[idx % 3]:
            # Utilisation de st.container avec bordure pour l'effet "Carte"
            with st.container(border=True):
                
                # 1. Badge Source
                badge_class = "avito" if "avito" in row.source.lower() else "marocannonces"
                st.markdown(f'<span class="source-badge {badge_class}">{row.source}</span>', unsafe_allow_html=True)
                
                # 2. Image
                img_url = row.image_url
                if not img_url or img_url == 'N/A' or pd.isna(img_url):
                    st.image("https://via.placeholder.com/300x200?text=Pas+d'image", use_container_width=True)
                else:
                    st.image(img_url, use_container_width=True)
                
                # 3. Titre
                st.markdown(f'<div class="ad-title">{row.titre}</div>', unsafe_allow_html=True)
                
                # 4. Prix
                price_display = row.prix if row.prix not in ['N/A', '', '0', 0] else "Sur demande"
                st.markdown(f'<div class="price-tag">{price_display}</div>', unsafe_allow_html=True)
                
                # 5. Localisation & Date
                st.markdown(f"""
                    <div class="meta-info">
                        <span>📍 {row.localisation}</span>
                        <span>•</span>
                        <span>🕒 {str(row.date_text)[:10]}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # 6. Bouton d'action
                st.write("") # Petit espacement
                st.link_button("Voir l'annonce", row.url, use_container_width=True)

elif df.empty:
    st.info("⏳ En attente de données... Assurez-vous que les producers Kafka tournent.")
else:
    st.warning("🚫 Aucune annonce ne correspond à vos filtres. Essayez d'élargir la recherche.")