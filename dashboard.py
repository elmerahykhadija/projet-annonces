import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import re
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Dashboard Analytics", page_icon="📊", layout="wide")

# --- FONCTIONS UTILITAIRES ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3307,
        user="user",
        password="password",
        database="avito_db"
    )

def clean_price(price_str):
    """Convertit le prix textuel (ex: '120 000 DH') en nombre (float)"""
    if not price_str or pd.isna(price_str) or 'sur demande' in str(price_str).lower():
        return 0.0
    # Garder uniquement les chiffres
    clean_str = re.sub(r'[^\d]', '', str(price_str))
    try:
        return float(clean_str)
    except:
        return 0.0

@st.cache_data(ttl=5)  # Cache de 5 secondes pour actualisation rapide
def load_data():
    conn = get_db_connection()
    query = "SELECT * FROM annonces"
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Nettoyage et conversion des données
    df['prix_num'] = df['prix'].apply(clean_price)
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df

# --- AUTO-REFRESH ---
# Placeholder pour le timer
placeholder = st.empty()

# Compteur de rafraîchissement dans session_state
if 'refresh_count' not in st.session_state:
    st.session_state.refresh_count = 0

# --- INTERFACE ---
st.title("📊 Dashboard - Analyse du Marché")
col_title1, col_title2 = st.columns([3, 1])
with col_title1:
    st.markdown("Vue d'ensemble des données collectées depuis **Avito** et **MarocAnnonces**.")
with col_title2:
    st.caption(f"🔄 Auto-refresh: 5s | Cycle #{st.session_state.refresh_count}")

try:
    df = load_data()

    if df.empty:
        st.warning("Aucune donnée disponible dans la base de données.")
    else:
        # --- 1. KPIs (Indicateurs Clés) ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Annonces", len(df))
        col2.metric("Prix Moyen", f"{df[df['prix_num'] > 0]['prix_num'].mean():,.0f} DH".replace(",", " "))
        col3.metric("Nb de Villes", df['localisation'].nunique())
        col4.metric("Dernière MAJ", df['created_at'].max().strftime('%H:%M:%S'))

        st.divider()

        # --- 2. GRAPHIQUES ---
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Répartition par Source")
            fig_source = px.pie(df, names='source', title='Part de marché (Avito vs MarocAnnonces)', hole=0.4)
            st.plotly_chart(fig_source, use_container_width=True)

        with c2:
            st.subheader("Top Catégories")
            category_counts = df['category'].value_counts().reset_index()
            category_counts.columns = ['Catégorie', 'Nombre']
            fig_cat = px.bar(category_counts, x='Catégorie', y='Nombre', color='Catégorie', title="Nombre d'annonces par catégorie")
            st.plotly_chart(fig_cat, use_container_width=True)

        # --- 3. ANALYSE DES PRIX ---
        st.subheader("💰 Distribution des Prix par Catégorie")
        
        # Filtre pour enlever les prix extrêmes ou nuls pour le graphique
        df_filtered_price = df[(df['prix_num'] > 100) & (df['prix_num'] < 5000000)] # Ex: entre 100 et 5M DH
        
        fig_box = px.box(df_filtered_price, x="category", y="prix_num", color="source", 
                         title="Distribution des prix (Boxplot)", points="outliers")
        st.plotly_chart(fig_box, use_container_width=True)

        # --- 4. TABLEAU DE DONNÉES ---
        st.subheader("📋 Dernières Données Brutes")
        st.dataframe(df[['source', 'category', 'titre', 'prix', 'localisation', 'created_at']].sort_values(by='created_at', ascending=False).head(50))

except Exception as e:
    st.error(f"Erreur de connexion à la base de données : {e}")

# --- AUTO-REFRESH LOGIC ---
time.sleep(5)
st.session_state.refresh_count += 1
st.rerun()