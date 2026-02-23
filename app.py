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

# --- 2. STYLE CSS 
st.markdown("""
<style>
    /* Import de la police Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC;
    }

    /* Style du Header Principal */
    .main-title {
        font-weight: 800;
        letter-spacing: -1px;
        color: #1E293B;
        margin-bottom: 5px;
        font-size: 2.5rem;
    }

    /* Conteneur de la Carte (Ad Card) */
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
        background-color: white;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        padding: 0px !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        border-color: #3B82F6 !important;
    }

    /* Images de l'annonce */
    div[data-testid="stImage"] img {
        border-radius: 16px 16px 0 0 !important;
        height: 200px !important;
        object-fit: cover;
    }

    /* Badges de source raffinés */
    .source-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: white;
        margin-bottom: 10px;
    }
    .avito { background: linear-gradient(135deg, #3B82F6, #1D4ED8); }
    .marocannonces { background: linear-gradient(135deg, #F59E0B, #D97706); }

    /* Contenu texte de la carte */
    .card-content {
        padding: 0 15px 15px 15px;
    }

    .ad-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1E293B;
        height: 2.8em;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        line-height: 1.4;
    }

    .price-tag {
        font-size: 1.3rem;
        font-weight: 700;
        color: #059669;
        margin: 12px 0;
    }

    .meta-info {
        font-size: 0.85rem;
        color: #64748B;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 15px;
    }

    /* Style des boutons native override */
    .stLinkButton > a {
        background-color: #F1F5F9 !important;
        color: #475569 !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 10px !important;
        transition: all 0.2s;
    }
    
    .stLinkButton > a:hover {
        background-color: #1E293B !important;
        color: white !important;
        border-color: #1E293B !important;
    }

    /* Sidebar élégante */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
    }
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown p, 
    section[data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Input fields sidebar */
    .stTextInput input, .stSelectbox div {
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. FONCTIONS BACKEND ---

def get_db_connection():
    """Connexion à la base de données MySQL"""
    conn = mysql.connector.connect(
        host="localhost",
        port=3307,
        user="user",
        password="password",
        database="avito_db",
        connection_timeout=5
    )
    return conn

def clean_price(price_str):
    if not price_str or pd.isna(price_str): return 0.0
    clean_str = re.sub(r'[^\d]', '', str(price_str))
    try:
        return float(clean_str)
    except:
        return 0.0

@st.cache_data(ttl=60)
def load_data():
    try:
        conn = get_db_connection()
        query = "SELECT * FROM annonces ORDER BY timestamp_scraped DESC LIMIT 2000"
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            df['prix_num'] = df['prix'].apply(clean_price)
            df['localisation'] = df['localisation'].fillna('Maroc')
            df['category'] = df['category'].fillna('Divers')
            df['source_clean'] = df['source'].astype(str).str.lower().str.replace(' ', '')
        return df
    except Exception as e:
        st.error(f"⚠️ Erreur de connexion : {e}")
        return pd.DataFrame()

# --- 4. CHARGEMENT ET SIDEBAR ---

df = load_data()

with st.sidebar:
    st.markdown("# ⚙️ Configuration")
    st.markdown("Personnalisez votre recherche")
    st.divider()
    
    if not df.empty:
        # Recherche par mot-clé
        search_query = st.text_input("🔍 Recherche rapide", placeholder="Ex: BMW, iPhone...")
        
        # Filtres principaux
        selected_category = st.selectbox("📂 Catégorie", ["Toutes"] + sorted(df['category'].unique().tolist()))
        selected_city = st.selectbox("📍 Ville", ["Toutes"] + sorted(df['localisation'].unique().tolist()))
        
        # Budget
        max_val_db = int(df['prix_num'].max()) if not df.empty and df['prix_num'].max() > 0 else 100000
        budget = st.number_input("💰 Budget Max (DH)", min_value=0, value=max_val_db, step=500)
        
        # Sources
        st.markdown("---")
        st.markdown("**🌐 Plateformes**")
        col1, col2 = st.columns(2)
        use_avito = col1.checkbox("Avito", True)
        use_ma = col2.checkbox("M.Annonces", True)
        
        selected_sources = []
        if use_avito: selected_sources.append('avito')
        if use_ma: selected_sources.append('marocannonces')

        st.divider()
        st.caption(f"Status: Connecté • {len(df)} annonces")

# --- 5. LOGIQUE DE FILTRAGE ---
if not df.empty:
    filtered_df = df.copy()
    if selected_category != "Toutes":
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if selected_city != "Toutes":
        filtered_df = filtered_df[filtered_df['localisation'] == selected_city]
    
    # Filtrage par source
    filtered_df = filtered_df[filtered_df['source'].str.lower().str.contains('|'.join(selected_sources))]
    
    # Filtrage prix
    filtered_df = filtered_df[filtered_df['prix_num'] <= budget]
    
    # Filtrage recherche
    if search_query:
        filtered_df = filtered_df[filtered_df['titre'].str.contains(search_query, case=False, na=False)]
else:
    filtered_df = pd.DataFrame()

# --- 6. INTERFACE PRINCIPALE ---

st.markdown('<h1 class="main-title">🛒 Marketplace Aggregator</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #64748B; font-size: 1.1rem; margin-bottom: 2rem;">Les meilleures opportunités d\'Avito et MarocAnnonces en un seul endroit.</p>', unsafe_allow_html=True)

if not filtered_df.empty:
    # Affichage des résultats
    cols = st.columns(3)
    
    for idx, row in enumerate(filtered_df.itertuples()):
        with cols[idx % 3]:
            with st.container(border=True):
                # Image
                img_url = row.image_url
                if not img_url or img_url in ['N/A', ''] or pd.isna(img_url):
                    st.image("https://via.placeholder.com/400x250?text=Image+Indisponible", use_container_width=True)
                else:
                    st.image(img_url, use_container_width=True)
                
                # Contenu de la carte
                st.markdown('<div class="card-content">', unsafe_allow_html=True)
                
                # Badge
                badge_class = "avito" if "avito" in row.source.lower() else "marocannonces"
                st.markdown(f'<span class="source-badge {badge_class}">{row.source}</span>', unsafe_allow_html=True)
                
                # Titre et Prix
                st.markdown(f'<div class="ad-title">{row.titre}</div>', unsafe_allow_html=True)
                price_display = row.prix if row.prix not in ['N/A', '', '0', 0] else "Prix non spécifié"
                st.markdown(f'<div class="price-tag">{price_display}</div>', unsafe_allow_html=True)
                
                # Meta Infos
                date_val = str(row.date_text)[:10] if hasattr(row, 'date_text') else "Récemment"
                st.markdown(f"""
                    <div class="meta-info">
                        <span>📍 {row.localisation}</span>
                        <span>•</span>
                        <span>🕒 {date_val}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Bouton
                st.link_button("Explorer l'offre", row.url, use_container_width=True)

elif df.empty:
    st.info("💡 En attente de données... Vérifiez la connexion à votre base MySQL (Port 3307).")
else:
    st.warning("🧐 Aucune annonce ne correspond à vos critères. Essayez d'ajuster les filtres.")

