import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import unicodedata
from io import BytesIO
import os
import base64

# ==============================================================================
# 1. CONFIGURAZIONE PAGINA (PRIMA ISTRUZIONE OBBLIGATORIA)
# ==============================================================================
st.set_page_config(
    page_title="Saleszone | Suite Operativa",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 2. STILE E BRANDING (CSS SALESZONE)
# ==============================================================================
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
            color: #2940A8;
        }
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #F4F6FC;
            border-right: 1px solid #DBDBDB;
        }
        /* Titoli */
        h1, h2, h3, h4 {
            color: #2940A8 !important;
            font-weight: 700;
        }
        /* Bottoni */
        div.stButton > button:first-child {
            background-color: #FA7838;
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: 600;
            padding: 0.5rem 1rem;
        }
        div.stButton > button:first-child:hover {
            background-color: #e06020;
            color: white;
        }
        /* Metriche */
        [data-testid="stMetricValue"] {
            color: #FA7838 !important;
            font-weight: 700;
        }
        [data-testid="stMetricLabel"] {
            color: #2940A8 !important;
        }
        /* Logo Sidebar Custom */
        .sidebar-logo-container {
            padding: 20px 0;
            margin-bottom: 20px;
            text-align: left;
        }
        .sidebar-logo-main {
            font-size: 32px;
            font-weight: 800;
            color: #2940A8;
            line-height: 1;
            letter-spacing: -1px;
        }
        .sidebar-logo-main span {
            color: #FA7838;
        }
        .sidebar-tagline {
            font-size: 10px;
            color: #2940A8;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            line-height: 1.4;
        }
        
        /* Tabelle */
        [data-testid="stDataFrame"] {
            border: 1px solid #DBDBDB;
            border-radius: 8px;
        }
        /* Expander */
        .streamlit-expanderHeader {
            font-weight: 600;
            color: #2940A8;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 3. UTILITIES GLOBALI (CARICAMENTO ROBUSTO)
# ==============================================================================
def load_data_robust(file):
    """
    Funzione avanzata per leggere CSV/Excel.
    Rileva automaticamente se il file ha una riga di metadata iniziale (comune nei report Amazon)
    e la salta per leggere correttamente le intestazioni.
    """
    if file is None: return None
    
    # 1. Gestione Excel
    if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
        try:
            return pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            st.error(f"Errore lettura Excel: {e}")
            return None

    # 2. Gestione CSV (Analisi intelligente della prima riga)
    if file.name.endswith('.csv'):
        try:
            # Legge la prima riga per capire se è un'intestazione spuria (es. "Marchio=...")
            content = file.getvalue().decode('utf-8', errors='ignore')
            first_line = content.split('\n')[0]
            
            skip_rows = 0
            if "Marchio=" in first_line or "Periodo interessato=" in first_line:
                skip_rows = 1
            
            file.seek(0)
            
            # Tenta lettura standard utf-8
            try:
                df = pd.read_csv(file, encoding='utf-8', skiprows=skip_rows)
                if df.shape[1] > 1: return df
            except: pass
            
            # Tenta separatore ;
            file.seek(0)
            try:
                df = pd.read_csv(file, sep=';', encoding='utf-8', skiprows=skip_rows)
                if df.shape[1] > 1: return df
            except: pass
            
            # Tenta encoding latin1
            file.seek(0)
            try:
                df = pd.read_csv(file, sep=';', encoding='latin1', skiprows=skip_rows)
                if df.shape[1] > 1: return df
            except: pass
            
            # Ultimo tentativo
            file.seek(0)
            df = pd.read_csv(file, encoding='latin1', skiprows=skip_rows)
            return df

        except Exception as e:
            st.error(f"Impossibile leggere il file CSV. Errore: {e}")
            return None
            
    return None

def clean_columns(df):
    """Pulisce i nomi delle colonne da spazi extra e caratteri invisibili."""
    if df is not None:
        df.columns = df.columns.str.strip().str.replace("\ufeff", "")
    return df

# ==============================================================================
# 4. MODULI APPLICAZIONE
# ==============================================================================

# --- HOME ---
def show_home():
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("""
        <div style='background-color: #2940A8; padding: 30px; border-radius: 15px; text-align: center;'>
            <h1 style='color: white !important; margin: 0; font-size: 60px;'>S<span style='color: #FA7838;'>Z</span></h1>
            <p style='color: white; margin: 10px 0 0 0; font-size: 14px; letter-spacing: 4px; font-weight: 600;'>SALESZONE</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.title("Benvenuto in Saleszone")
        st.markdown("### Il tuo spazio di crescita su Amazon.")
        st.write("""
        Questa suite operativa integra tutti gli strumenti necessari per l'analisi e l'ottimizzazione 
        del tuo account Amazon Seller. Seleziona uno strumento dalla sidebar per iniziare.
        """)
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("🎯 **Missione**\n\nSupportare i brand con consulenza strategica one-to-one e autentica.")
    with c2:
        st.success("💎 **Valori**\n\nProfessionalità, Autenticità, Trasparenza, Disciplina.")
    with c3:
        st.warning("🤝 **Metodo**\n\nNessun intermediario, solo risultati concreti e misurabili.")

# --- PPC OPTIMIZER ---
def show_ppc_optimizer():
    st.title("📊 Saleszone Ads Optimizer")
    st.write("Carica i report Amazon PPC, analizza KPI e genera suggerimenti intelligenti.")

    # === UPLOAD FILE ===
    st.subheader("📂 Carica i tuoi report")
    col1, col2 = st.columns(2)
    with col1:
        search_term_file = st.file_uploader("Carica Report Search Term (Obbligatorio)", type=["csv", "xlsx"])
    with col2:
        placement_file = st.file_uploader("Carica Report Placement (Opzionale)", type=["csv", "xlsx"])

    # === FILTRI GLOBALI ===
    c1, c2, c3 = st.columns(3)
    acos_target = c1.number_input("🎯 ACOS Target (%)", min_value=1, max_value=100, value=30)
    click_min = c2.number_input("⚠️ Click minimo per Search Terms senza vendite", min_value=1, value=10)
    percent_threshold = c3.number_input("📊 % Spesa per segnalazione critica", min_value=1, max_value=100, value=10)

    if search_term_file:
        df = load_data_robust(search_term_file)
        if df is None: return
        df = clean_columns(df)

        # Mapping colonne
        mapping = {
            'Nome portafoglio': 'Portfolio', 'Portfolio name': 'Portfolio',
            'Nome campagna': 'Campaign', 'Campaign Name': 'Campaign',
            'Targeting': 'Keyword', 
            'Termine ricerca cliente': 'Search Term', 'Customer Search Term': 'Search Term',
            'Impressioni': 'Impressions', 'Impressions': 'Impressions',
            'Clic': 'Clicks', 'Clicks': 'Clicks',
            'Spesa': 'Spend', 'Spend': 'Spend', 'Costo': 'Spend',
            'Vendite totali (€) 7 giorni': 'Sales', '7 Day Total Sales': 'Sales', 'Vendite': 'Sales',
            'Totale ordini (#) 7 giorni': 'Orders', '7 Day Total Orders': 'Orders', 'Ordini': 'Orders'
        }
        df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)

        # Colonne mancanti
        required_cols = ['Impressions', 'Clicks', 'Spend', 'Sales', 'Orders']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0
            else:
                if df[col].dtype == object:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                else:
                    df[col] = df[col].fillna(0)

        # Gestione Nomi Mancanti
        if 'Portfolio' not in df.columns: df['Portfolio'] = 'N/A'
        if 'Campaign' not in df.columns: df['Campaign'] = 'Sconosciuta'
        df['Portfolio'].fillna('Nessun Portafoglio', inplace=True)

        # KPI per riga
        df['CPC'] = df['Spend'] / df['Clicks'].replace(0, 1)
        df['CTR'] = (df['Clicks'] / df['Impressions'].replace(0, 1)) * 100
        df['CR'] = (df['Orders'] / df['Clicks'].replace(0, 1)) * 100
        df['ACOS'] = df.apply(lambda r: (r['Spend'] / r['Sales'] * 100) if r['Sales'] > 0 else None, axis=1)

        # KPI globali
        total_spend = df['Spend'].sum()
        total_sales = df['Sales'].sum()
        total_clicks = df['Clicks'].sum()
        total_impressions = df['Impressions'].sum()
        total_orders = df['Orders'].sum()

        avg_acos = (total_spend / total_sales * 100) if total_sales > 0 else 0
        ctr_global = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cr_global = (total_orders / total_clicks * 100) if total_clicks > 0 else 0

        threshold_spesa = total_spend * (percent_threshold / 100)

        # KPI VISUAL
        st.markdown("### 📌 KPI Principali")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Spesa Totale", f"€{total_spend:,.2f}")
        col2.metric("Vendite Totali", f"€{total_sales:,.2f}")
        col3.metric("ACOS Medio", f"{avg_acos:.2f}%")
        col4.metric("CTR Totale", f"{ctr_global:.2f}%")
        col5.metric("CR Totale", f"{cr_global:.2f}%")

        # PANORAMICA PORTAFOGLI
        st.subheader("📦 Panoramica per Portafoglio")
        portfolio_group = df.groupby('Portfolio', as_index=False).agg({
            'Impressions': 'sum', 'Clicks': 'sum', 'Spend': 'sum', 'Sales': 'sum', 'Orders': 'sum'
        })
        portfolio_group['CPC'] = portfolio_group['Spend'] / portfolio_group['Clicks'].replace(0, 1)
        portfolio_group['CTR'] = (portfolio_group['Clicks'] / portfolio_group['Impressions'].replace(0, 1)) * 100
        portfolio_group['CR'] = (portfolio_group['Orders'] / portfolio_group['Clicks'].replace(0, 1)) * 100
        portfolio_group['ACOS'] = portfolio_group.apply(lambda r: (r['Spend'] / r['Sales'] * 100) if r['Sales'] > 0 else None, axis=1)
        st.dataframe(portfolio_group.style.format({
            'Spend': '€{:.2f}', 'Sales': '€{:.2f}', 'CPC': '€{:.2f}', 'CTR': '{:.2f}%', 'CR': '{:.2f}%', 'ACOS': lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
        }), use_container_width=True)

        # PANORAMICA CAMPAGNE
        st.subheader("📊 Panoramica per Campagna")
        portfolio_options = ["Tutti"] + sorted(df['Portfolio'].unique().tolist())
        selected_portfolio_for_campaign = st.selectbox("Filtra per Portafoglio", portfolio_options, key="portfolio_campaign")
        
        df_campaign_filtered = df.copy()
        if selected_portfolio_for_campaign != "Tutti":
            df_campaign_filtered = df_campaign_filtered[df_campaign_filtered['Portfolio'] == selected_portfolio_for_campaign]

        campaign_group = df_campaign_filtered.groupby('Campaign', as_index=False).agg({
            'Impressions': 'sum', 'Clicks': 'sum', 'Spend': 'sum', 'Sales': 'sum', 'Orders': 'sum'
        })
        campaign_group['CPC'] = campaign_group['Spend'] / campaign_group['Clicks'].replace(0, 1)
        campaign_group['CTR'] = (campaign_group['Clicks'] / campaign_group['Impressions'].replace(0, 1)) * 100
        campaign_group['CR'] = (campaign_group['Orders'] / campaign_group['Clicks'].replace(0, 1)) * 100
        campaign_group['ACOS'] = campaign_group.apply(lambda r: (r['Spend'] / r['Sales'] * 100) if r['Sales'] > 0 else None, axis=1)

        st.dataframe(campaign_group.style.format({
            'Spend': '€{:.2f}', 'Sales': '€{:.2f}', 'CPC': '€{:.2f}', 'CTR': '{:.2f}%', 'CR': '{:.2f}%', 'ACOS': lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
        }), use_container_width=True)

        # DETTAGLIO SEARCH TERMS
        st.subheader("🔍 Dettaglio Search Terms per Campagna")
        c1, c2 = st.columns(2)
        portfolio_filter = c1.selectbox("Seleziona Portafoglio", ["Tutti"] + sorted(df['Portfolio'].unique()), key="portfolio_terms")
        
        campaign_options = df['Campaign'].unique().tolist()
        if portfolio_filter != "Tutti":
            campaign_options = df[df['Portfolio'] == portfolio_filter]['Campaign'].unique().tolist()
        campaign_filter = c2.selectbox("Seleziona Campagna", ["Tutte"] + sorted(campaign_options), key="campaign_terms")

        df_filtered_terms = df.copy()
        if portfolio_filter != "Tutti":
            df_filtered_terms = df_filtered_terms[df_filtered_terms['Portfolio'] == portfolio_filter]
        if campaign_filter != "Tutte":
            df_filtered_terms = df_filtered_terms[df_filtered_terms['Campaign'] == campaign_filter]

        if not df_filtered_terms.empty:
            cols_to_show = ['Search Term', 'Keyword', 'Campaign', 'Impressions', 'Clicks', 'Spend', 'Sales', 'Orders', 'CPC', 'CTR', 'CR', 'ACOS']
            cols_to_show = [c for c in cols_to_show if c in df_filtered_terms.columns]
            st.dataframe(df_filtered_terms[cols_to_show].head(100).style.format({
                'Spend': '€{:.2f}', 'Sales': '€{:.2f}', 'CPC': '€{:.2f}', 'CTR': '{:.2f}%', 'CR': '{:.2f}%', 'ACOS': lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
            }), height=500)

        # SEARCH TERMS SENZA VENDITE
        st.subheader(f"⚠️ Search Terms senza vendite (>{click_min} click)")
        waste_terms = df[(df['Sales'] == 0) & (df['Clicks'] >= click_min)]
        st.dataframe(waste_terms[['Portfolio', 'Search Term', 'Keyword', 'Campaign', 'Clicks', 'Spend']].sort_values(by='Spend', ascending=False), use_container_width=True)

        # SUGGERIMENTI AI
        st.subheader("🤖 Suggerimenti AI")
        suggestions = []
        for _, row in campaign_group.iterrows():
            if row['Sales'] == 0 and row['Spend'] >= threshold_spesa:
                suggestions.append(f"🔴 Blocca campagna **{row['Campaign']}**: spesa €{row['Spend']:.2f} senza vendite")
            elif row['Sales'] == 0 and row['Spend'] >= 5:
                suggestions.append(f"🟠 Valuta campagna **{row['Campaign']}**: spesa €{row['Spend']:.2f} senza vendite")
            elif row['Sales'] > 0 and row['ACOS'] > acos_target:
                suggestions.append(f"🟡 Ottimizza bid in **{row['Campaign']}**: ACOS {row['ACOS']:.2f}% > target {acos_target}%")
        
        if suggestions:
            for s in suggestions: st.markdown(f"- {s}")
        else:
            st.success("Tutto sotto controllo in base ai parametri attuali.")

        # TOP 3 OTTIMIZZAZIONI
        st.subheader("🔥 Cosa ottimizzare subito")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Portafogli peggiori (Top 3)**")
            pf_sorted = portfolio_group.copy().sort_values(by=['Sales', 'Spend'], ascending=[True, False]).head(3)
            for _, row in pf_sorted.iterrows():
                acos_display = f"{row['ACOS']:.2f}%" if pd.notna(row['ACOS']) else "N/A"
                st.error(f"{row['Portfolio']} (Spesa: €{row['Spend']:.2f}, ACOS: {acos_display})")
        
        with c2:
            st.markdown("**Campagne peggiori (Top 3)**")
            camp_sorted = campaign_group.copy().sort_values(by=['Sales', 'Spend'], ascending=[True, False]).head(3)
            for _, row in camp_sorted.iterrows():
                acos_display = f"{row['ACOS']:.2f}%" if pd.notna(row['ACOS']) else "N/A"
                st.error(f"{row['Campaign']} (Spesa: €{row['Spend']:.2f}, ACOS: {acos_display})")

# --- BRAND ANALYTICS ---
def show_brand_analytics():
    st.title("📈 Brand Analytics Insights")
    brand_file = st.file_uploader("Carica il file Brand Analytics (CSV/XLSX)", type=["csv", "xlsx"])

    def norm(s: str) -> str:
        """Funzione norm esatta dal Codice Madre"""
        return (str(s).strip().lower()
            .replace("%", "").replace(":", "").replace("(", "").replace(")", "")
            .replace("/", " ").replace("-", " ").replace("  ", " ").replace(" ", "_"))

    def safe_div(a, b):
        if np.isscalar(a) and np.isscalar(b):
            return float(a) / float(b) if b not in [0, None, np.nan] else 0.0
        a = pd.to_numeric(a, errors="coerce")
        b = pd.to_numeric(b, errors="coerce").replace({0: np.nan})
        return (a / b).fillna(0)

    if brand_file:
        df_raw = load_data_robust(brand_file)
        if df_raw is None: return
        df_raw = clean_columns(df_raw)

        idx = {norm(c): c for c in df_raw.columns}
        
        def pick(col_index, *aliases):
            for a in aliases:
                n = norm(a)
                if n in col_index: return col_index[n]
            return None

        # Risoluzione colonne esatta come Codice Madre
        c_query = pick(idx, "Query di ricerca", "search_query", "Termine di ricerca", "query_di_ricerca")
        c_volume = pick(idx, "Volume query di ricerca", "search_query_volume", "Volume di ricerca", "volume_query_di_ricerca")
        c_imp_tot = pick(idx, "Impressioni: conteggio totale", "search_funnel_impressions_total", "Impressioni totali", "impressioni_conteggio_totale")
        c_imp_asin = pick(idx, "Impressioni: numero ASIN", "impressioni_numero_asin", "Impressioni ASIN", "impressioni_conteggio_marchio", "impressioni_conteggio_asin")
        c_clk_tot = pick(idx, "Clic: conteggio totale", "search_funnel_clicks_total", "Clic totali", "clic_conteggio_totale")
        c_clk_asin = pick(idx, "Clic: numero di ASIN", "clic_numero_asin", "Clic ASIN", "clic_conteggio_marchio", "clic_numero_di_asin")
        c_add_tot = pick(idx, "Aggiunte al carrello: conteggio totale", "search_funnel_add_to_carts_total", "aggiunte_al_carrello_conteggio_totale")
        c_add_asin = pick(idx, "Aggiunte al carrello: numero ASIN", "search_funnel_add_to_carts_brand_asin_count", "aggiunte_al_carrello_conteggio_marchio", "aggiunte_al_carrello_numero_asin")
        c_buy_tot = pick(idx, "Acquisti: conteggio totale", "search_funnel_purchases_total", "acquisti_conteggio_totale")
        c_buy_asin = pick(idx, "Acquisti: numero ASIN", "search_funnel_purchases_brand_asin_count", "acquisti_conteggio_marchio", "acquisti_numero_asin")

        if not c_query:
            st.error("Colonna 'Query di ricerca' non trovata. Verifica che il file non sia corrotto o di formato diverso.")
            st.write("Colonne trovate:", list(df_raw.columns))
            return

        base = pd.DataFrame()
        base["Query"] = df_raw[c_query]
        base["Volume"] = pd.to_numeric(df_raw[c_volume], errors='coerce').fillna(0) if c_volume else 0
        
        # Helper per estrarre valori
        def get_col(c): return pd.to_numeric(df_raw[c], errors='coerce').fillna(0) if c else 0
        
        base["Impr_tot"] = get_col(c_imp_tot)
        base["Impr_asin"] = get_col(c_imp_asin)
        base["Click_tot"] = get_col(c_clk_tot)
        base["Click_asin"] = get_col(c_clk_asin)
        base["ATC_tot"] = get_col(c_add_tot)
        base["ATC_asin"] = get_col(c_add_asin)
        base["Buy_tot"] = get_col(c_buy_tot)
        base["Buy_asin"] = get_col(c_buy_asin)

        # Calcoli Metriche
        out = pd.DataFrame()
        out["Query"] = base["Query"]
        out["Volume"] = base["Volume"]
        out["Impression Share Asin"] = safe_div(base["Impr_asin"], base["Impr_tot"])
        out["CTR Market"] = safe_div(base["Click_tot"], base["Impr_tot"])
        out["CTR Asin"] = safe_div(base["Click_asin"], base["Impr_asin"])
        out["CR Market"] = safe_div(base["Buy_tot"], base["Click_tot"])
        out["CR Asin"] = safe_div(base["Buy_asin"], base["Click_asin"])
        
        # Formattazione
        display = out.copy()
        st.subheader("Risultati Analisi")
        st.dataframe(display.head(50), use_container_width=True)

        # Download
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            display.to_excel(writer, index=False)
        st.download_button("Scarica Analisi (Excel)", buffer.getvalue(), "brand_analytics.xlsx")

        # Dashboard Totale
        st.subheader("Cruscotto Totale")
        c1, c2, c3 = st.columns(3)
        c1.metric("Volume Totale", f"{int(base['Volume'].sum()):,}")
        c2.metric("Impression Share Media", f"{out['Impression Share Asin'].mean()*100:.2f}%")
        c3.metric("CTR Asin Medio", f"{out['CTR Asin'].mean()*100:.2f}%")

# --- SQP (FUNZIONE CORRETTA CON CR MARKET E MARCHIO) ---
def show_sqp():
    st.title("🔎 SQP – Search Query Performance")
    sqp_file = st.file_uploader("Carica il file Search Query Performance (.csv)", type=["csv"])

    if sqp_file:
        df_sqp = load_data_robust(sqp_file)
        if df_sqp is None: return
        df_sqp = clean_columns(df_sqp)

        def norm_col(s): 
            return (str(s).strip().lower()
                .replace("%","").replace(":","").replace("(","").replace(")","")
                .replace("/","").replace("-","").replace("  "," ").replace(" ","_"))
        
        col_index = {norm_col(c): c for c in df_sqp.columns}
        
        def pick(*aliases):
            for a in aliases:
                key = norm_col(a)
                if key in col_index: return col_index[key]
            return None

        # Mappatura Esatta Codice Madre
        col_query = pick(
            "Query di ricerca", "search_query", "search_term", "Termine ricerca cliente"
        )
        col_imp_tot = pick(
            "Impressioni: conteggio totale", "search_funnel_impressions_total", 
            "Impressioni conteggio totale", "Impressions total"
        )
        col_imp_brand = pick(
            "Impressioni: conteggio marchio", "search_funnel_impressions_brand", 
            "Impressions brand", "Impressioni conteggio marchio"
        )
        col_clk_tot = pick(
            "Clic: conteggio totale", "search_funnel_clicks_total", 
            "Clicks total", "Clic conteggio totale"
        )
        col_clk_brand = pick(
            "Clic: conteggio marchio", "search_funnel_clicks_brand", 
            "Clicks brand", "Clic conteggio marchio"
        )
        col_buy_tot = pick(
            "Acquisti: conteggio totale", "search_funnel_purchases_total", 
            "Purchases total", "Acquisti conteggio totale"
        )
        col_buy_brand = pick(
            "Acquisti: conteggio marchio", "search_funnel_purchases_brand", 
            "Purchases brand", "Acquisti conteggio marchio"
        )

        if not col_query:
            st.error("Colonne minime non trovate. Verifica il file.")
            with st.expander("Colonne rilevate nel file"):
                st.write(list(df_sqp.columns))
            return

        # Calcoli
        num_cols = [col_imp_tot, col_imp_brand, col_clk_tot, col_clk_brand, col_buy_tot, col_buy_brand]
        for c in num_cols:
            if c: df_sqp[c] = pd.to_numeric(df_sqp[c], errors='coerce').fillna(0)

        # Formule Esatte Codice Madre
        if col_imp_tot and col_clk_tot:
            df_sqp["CTR MARKET"] = df_sqp[col_clk_tot] / df_sqp[col_imp_tot].replace(0, 1)
        if col_imp_brand and col_clk_brand:
            df_sqp["CTR MARCHIO"] = df_sqp[col_clk_brand] / df_sqp[col_imp_brand].replace(0, 1)
        if col_clk_tot and col_buy_tot:
            df_sqp["CR MARKET"] = df_sqp[col_buy_tot] / df_sqp[col_clk_tot].replace(0, 1)
        if col_clk_brand and col_buy_brand:
            df_sqp["CR MARCHIO"] = df_sqp[col_buy_brand] / df_sqp[col_clk_brand].replace(0, 1)
        
        st.subheader("📌 KPI di Sintesi")
        if col_imp_tot:
            tot_imp = df_sqp[col_imp_tot].sum()
            st.metric("Impressioni Totali", f"{int(tot_imp):,}")
        
        if col_clk_tot and col_imp_tot:
            tot_clk = df_sqp[col_clk_tot].sum()
            ctr_tot = (tot_clk / tot_imp * 100) if tot_imp > 0 else 0
            st.metric("CTR Medio Market", f"{ctr_tot:.2f}%")

        st.subheader("🔍 Anteprima Dati (con CR MARKET e MARCHIO)")
        st.dataframe(df_sqp.head(50), use_container_width=True)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_sqp.to_excel(writer, index=False)
        st.download_button("Scarica SQP Elaborato", buffer.getvalue(), "sqp_analysis.xlsx")

# --- GENERAZIONE CORRISPETTIVI ---
def show_invoices():
    st.title("📄 Generazione Corrispettivi Mensili")
    file = st.file_uploader("Carica il report Transazioni con IVA (.csv)", type=["csv"])

    if file:
        df_corr = load_data_robust(file)
        if df_corr is None: return
        df_corr = clean_columns(df_corr)

        # Filtro SALE
        if 'TRANSACTION_TYPE' in df_corr.columns:
            df_corr = df_corr[df_corr['TRANSACTION_TYPE'].astype(str).str.upper() == 'SALE']
        
        # Date
        date_col = None
        for c in df_corr.columns:
            if 'DATE' in c.upper() and 'COMPLETE' in c.upper(): date_col = c; break
        
        if not date_col:
            possible = [c for c in df_corr.columns if 'date' in c.lower() or 'data' in c.lower()]
            if possible: date_col = possible[0]
        
        if date_col:
            df_corr[date_col] = pd.to_datetime(df_corr[date_col], errors='coerce')
            df_corr = df_corr.dropna(subset=[date_col])
            df_corr = df_corr.sort_values(date_col)
            
            cols_amt = {
                'Netto': [c for c in df_corr.columns if 'VALUE_AMT_VAT_EXCL' in c],
                'IVA': [c for c in df_corr.columns if 'VAT_AMT' in c and 'VALUE' in c],
                'Lordo': [c for c in df_corr.columns if 'VALUE_AMT_VAT_INCL' in c]
            }
            
            col_netto = cols_amt['Netto'][0] if cols_amt['Netto'] else None
            col_iva = cols_amt['IVA'][0] if cols_amt['IVA'] else None
            col_lordo = cols_amt['Lordo'][0] if cols_amt['Lordo'] else None

            if col_netto and col_iva and col_lordo:
                for c in [col_netto, col_iva, col_lordo]:
                    if df_corr[c].dtype == object:
                        df_corr[c] = pd.to_numeric(df_corr[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

                df_group = df_corr.groupby(df_corr[date_col].dt.date).agg({
                    col_netto: 'sum',
                    col_iva: 'sum',
                    col_lordo: 'sum'
                }).reset_index()
                
                df_group.columns = ['Data', 'Netto', 'IVA', 'Lordo']

                st.subheader("📊 Riepilogo Giornaliero")
                st.dataframe(df_group.style.format({'Netto': '€{:.2f}', 'IVA': '€{:.2f}', 'Lordo': '€{:.2f}'}), use_container_width=True)
                
                tot_netto = df_group['Netto'].sum()
                tot_iva = df_group['IVA'].sum()
                tot_lordo = df_group['Lordo'].sum()
                st.success(f"**Totale Mese:** Netto €{tot_netto:.2f} | IVA €{tot_iva:.2f} | Lordo €{tot_lordo:.2f}")

                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_group.to_excel(writer, sheet_name="Riepilogo", index=False)
                    df_corr.to_excel(writer, sheet_name="Dettaglio", index=False)
                st.download_button("Scarica Corrispettivi (Excel)", buffer.getvalue(), "corrispettivi.xlsx")
            else:
                st.error("Colonne importi (Netto/IVA/Lordo) non trovate nel report standard.")
        else:
            st.error("Colonna Data non trovata.")

# --- INVENTARIO FBA ---
def show_inventory():
    st.title("📦 Controllo Inventario FBA")
    st.write("Identifica anomalie, KPI e genera report per reclami Amazon.")
    inventory_file = st.file_uploader("Carica Inventory Ledger (CSV/XLSX)", type=["csv", "xlsx"])

    if inventory_file:
        df_inv = load_data_robust(inventory_file)
        if df_inv is None: return
        df_inv = clean_columns(df_inv)
        df_inv.columns = df_inv.columns.str.lower()

        # Check colonne
        numeric_cols = ['starting warehouse balance', 'receipts', 'customer shipments', 'customer returns', 
                        'vendor returns', 'warehouse transfer in/out', 'found', 'lost', 'damaged', 
                        'disposed', 'ending warehouse balance']
        
        for c in numeric_cols:
            if c in df_inv.columns:
                df_inv[c] = pd.to_numeric(df_inv[c], errors='coerce').fillna(0)

        # Filtri base
        if 'date' in df_inv.columns: df_inv['date'] = pd.to_datetime(df_inv['date'], errors='coerce')
        
        # KPI Globali
        st.subheader("📊 KPI Globali")
        c1, c2, c3 = st.columns(3)
        start = df_inv['starting warehouse balance'].sum() if 'starting warehouse balance' in df_inv.columns else 0
        end = df_inv['ending warehouse balance'].sum() if 'ending warehouse balance' in df_inv.columns else 0
        receipts = df_inv['receipts'].sum() if 'receipts' in df_inv.columns else 0
        
        c1.metric("Starting Balance", f"{int(start)}")
        c2.metric("Ending Balance", f"{int(end)}")
        c3.metric("Receipts", f"{int(receipts)}")

        # Logica Anomalia (Delta)
        if 'ending warehouse balance' in df_inv.columns:
            cols_inc = [c for c in ['receipts', 'customer returns', 'found'] if c in df_inv.columns]
            cols_dec = [c for c in ['customer shipments', 'lost', 'damaged', 'disposed'] if c in df_inv.columns]
            
            df_inv['inc'] = df_inv[cols_inc].sum(axis=1)
            df_inv['dec'] = df_inv[cols_dec].sum(axis=1).abs()
            
            df_inv['ending_teorico'] = df_inv.get('starting warehouse balance', 0) + df_inv['inc'] - df_inv['dec']
            df_inv['delta'] = df_inv['ending warehouse balance'] - df_inv['ending_teorico']
            
            anomalies = df_inv[df_inv['delta'].abs() > 0.1].copy()
            
            st.subheader(f"📌 Anomalie Rilevate: {len(anomalies)}")
            if not anomalies.empty:
                st.dataframe(anomalies)
                
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    anomalies.to_excel(writer, index=False, sheet_name="Anomalie")
                st.download_button("Scarica Report Reclami (Excel)", buffer.getvalue(), "reclami_fba.xlsx")
            else:
                st.success("Nessuna anomalia significativa rilevata.")

# --- FUNNEL AUDIT ---
def show_funnel_audit():
    st.title("🧭 PPC Funnel Audit")
    st.caption("Carica File Macro per mappare il funnel.")
    
    macro_file = st.file_uploader("File Macro (Campagne)", type=["csv", "xlsx"])
    
    if macro_file:
        df = load_data_robust(macro_file)
        if df is None: return
        df = clean_columns(df)

        def pick(df, candidates):
            for c in candidates:
                for col in df.columns:
                    if c.lower() in col.lower(): return col
            return None

        c_name = pick(df, ["Campagne", "Campaign", "Nome campagna"])
        c_spend = pick(df, ["Spesa", "Spend", "Costo"])
        c_sales = pick(df, ["Vendite", "Sales"])

        if not c_name or not c_spend:
            st.error("Colonne essenziali (Nome Campagna, Spesa) non trovate.")
            return

        df['Spend'] = pd.to_numeric(df[c_spend].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
        df['Sales'] = pd.to_numeric(df[c_sales].astype(str).str.replace(',','.'), errors='coerce').fillna(0) if c_sales else 0

        def get_layer(name):
            n = str(name).upper()
            if re.search(r"SBV|VIDEO", n): return "MOFU (Video)"
            if re.search(r"BRAND|PROTECTION|DEFENSE", n): return "BOFU (Brand)"
            if re.search(r"COMPETITOR|PAT|ASIN", n): return "MOFU (Competitor)"
            if re.search(r"EXACT|ESATTA", n): return "BOFU (Exact)"
            if re.search(r"BROAD|PHRASE|GENERIC|AUTO|CATEGORY", n): return "TOFU (Discovery)"
            return "TOFU (Altro)"

        df['Layer'] = df[c_name].apply(get_layer)
        
        kpi = df.groupby('Layer')[['Spend', 'Sales']].sum().reset_index()
        kpi['ROAS'] = kpi['Sales'] / kpi['Spend'].replace(0, 1)
        
        st.subheader("Distribuzione Budget Funnel")
        c1, c2 = st.columns([2, 1])
        with c1:
            try:
                import plotly.express as px
                fig = px.funnel(kpi, x='Spend', y='Layer', title="Spesa per Livello")
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.bar_chart(kpi.set_index('Layer')['Spend'])
        
        with c2:
            st.dataframe(kpi.style.format({'Spend': '€{:.2f}', 'Sales': '€{:.2f}', 'ROAS': '{:.2f}'}))

# ==============================================================================
# 5. MAIN NAVIGATOR
# ==============================================================================
def main():
    with st.sidebar:
        # LOGO HTML GENERATO VIA CSS (Più nitido e mai tagliato)
        st.markdown("""
        <div class="sidebar-logo-container">
            <div class="sidebar-logo-main">S<span>Z</span> SALESZONE</div>
            <div class="sidebar-tagline">Il tuo spazio di crescita su Amazon</div>
        </div>
        """, unsafe_allow_html=True)
        
        MENU_VOCI = [
            "Home",
            "PPC Optimizer",
            "Brand Analytics Insights",
            "SQP – Search Query Performance",
            "Generazione Corrispettivi",
            "Controllo Inventario FBA",
            "Funnel Audit"
        ]
        
        selected = st.radio("Naviga", MENU_VOCI, label_visibility="collapsed")
        
        st.markdown("---")
        st.caption("© 2025 Saleszone Agency")

    if selected == "Home": show_home()
    elif selected == "PPC Optimizer": show_ppc_optimizer()
    elif selected == "Brand Analytics Insights": show_brand_analytics()
    elif selected == "SQP – Search Query Performance": show_sqp()
    elif selected == "Generazione Corrispettivi": show_invoices()
    elif selected == "Controllo Inventario FBA": show_inventory()
    elif selected == "Funnel Audit": show_funnel_audit()

if __name__ == "__main__":
    main()
