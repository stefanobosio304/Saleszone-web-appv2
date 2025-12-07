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
# 1. CONFIGURAZIONE PAGINA
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
        /* Tabelle */
        [data-testid="stDataFrame"] {
            border: 1px solid #DBDBDB;
            border-radius: 8px;
        }
        /* Expander Guida */
        .streamlit-expanderHeader {
            font-weight: 600;
            color: #2940A8;
            background-color: #F4F6FC;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 3. UTILITIES GLOBALI (CARICAMENTO ROBUSTO & IMMAGINI)
# ==============================================================================
def get_img_as_base64(file):
    """Converte immagine in stringa base64 per HTML."""
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

def load_data_robust(file):
    """Caricamento file CSV/Excel robusto (rileva separatori e metadata)."""
    if file is None: return None
    
    # Excel
    if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
        try:
            return pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            st.error(f"Errore lettura Excel: {e}")
            return None

    # CSV
    if file.name.endswith('.csv'):
        try:
            content = file.getvalue().decode('utf-8', errors='ignore')
            first_line = content.split('\n')[0]
            # Salta la prima riga se contiene metadati Amazon tipo "Marchio=..."
            skip_rows = 1 if ("Marchio=" in first_line or "Periodo" in first_line) else 0
            
            file.seek(0)
            try: return pd.read_csv(file, encoding='utf-8', skiprows=skip_rows)
            except: pass
            
            file.seek(0)
            try: return pd.read_csv(file, sep=';', encoding='utf-8', skiprows=skip_rows)
            except: pass
            
            file.seek(0)
            return pd.read_csv(file, sep=';', encoding='latin1', skiprows=skip_rows)
        except Exception as e:
            st.error(f"Errore CSV: {e}")
            return None
    return None

def clean_columns(df):
    if df is not None:
        df.columns = df.columns.str.strip().str.replace("\ufeff", "")
    return df

def download_excel(dfs_dict, filename):
    buffer = BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            for sheet_name, df in dfs_dict.items():
                safe_name = str(sheet_name)[:30]
                df.to_excel(writer, sheet_name=safe_name, index=False)
        st.download_button(
            label=f"📥 Scarica {filename}",
            data=buffer.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Errore download: {e}")

# ==============================================================================
# 4. MODULI APPLICAZIONE (LOGICA MADRE COMPLETA)
# ==============================================================================

# --- HOME ---
def show_home():
    col1, col2 = st.columns([1, 2])
    with col1:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
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
        Questa suite di strumenti è progettata per ottimizzare le tue performance, analizzare i dati
        e semplificare la gestione del tuo account Amazon Seller.
        """)
        
        with st.expander("📚 Come iniziare"):
            st.markdown("""
            1.  **Seleziona uno strumento** dal menu laterale a sinistra.
            2.  **Leggi la guida all'uso** (il box "ℹ️ Guida" in alto in ogni pagina).
            3.  **Carica i tuoi report** (CSV o Excel).
            4.  **Analizza i risultati** e scarica i report ottimizzati.
            """)
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("🎯 **Missione**\n\nSupportare i brand con consulenza strategica one-to-one e autentica.")
    with c2:
        st.success("💎 **Valori**\n\nProfessionalità, Autenticità, Trasparenza, Disciplina.")
    with c3:
        st.warning("🤝 **Metodo**\n\nNessun intermediario, solo risultati concreti e misurabili.")

# --- PPC OPTIMIZER (LOGICA COMPLETA) ---
def show_ppc_optimizer():
    st.title("📊 Saleszone Ads Optimizer")
    
    with st.expander("ℹ️ Guida all'uso: PPC Optimizer", expanded=False):
        st.markdown("""
        **File richiesto:** Report Termini di Ricerca (Sponsored Products).
        **Analisi:** KPI, Portafogli, Campagne, Sprechi, Suggerimenti AI.
        """)

    # === UPLOAD FILE ===
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

        # Mapping colonne (Completo come da codice originale)
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

        # Gestione colonne mancanti
        required_cols = ['Impressions', 'Clicks', 'Spend', 'Sales', 'Orders']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0
            else:
                if df[col].dtype == object:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                else: df[col] = df[col].fillna(0)

        df.fillna(0, inplace=True)
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

        st.markdown("### 📌 KPI Principali")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Spesa Totale", f"€{total_spend:,.2f}")
        k2.metric("Vendite Totali", f"€{total_sales:,.2f}")
        k3.metric("ACOS Medio", f"{avg_acos:.2f}%")
        k4.metric("CTR Totale", f"{ctr_global:.2f}%")
        k5.metric("CR Totale", f"{cr_global:.2f}%")

        # 1. PANORAMICA PORTAFOGLI
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

        # 2. PANORAMICA CAMPAGNE (Con Filtro Dinamico come da originale)
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

        # 3. DETTAGLIO SEARCH TERMS (Con doppio filtro)
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

        # 4. SEARCH TERMS SENZA VENDITE
        st.subheader(f"⚠️ Search Terms senza vendite (>{click_min} click)")
        waste_terms = df[(df['Sales'] == 0) & (df['Clicks'] >= click_min)]
        st.dataframe(waste_terms[['Portfolio', 'Search Term', 'Keyword', 'Campaign', 'Clicks', 'Spend']].sort_values(by='Spend', ascending=False), use_container_width=True)

        # 5. SUGGERIMENTI AI (Logica Madre)
        st.subheader("🤖 Suggerimenti AI")
        suggestions = []
        for _, row in df.groupby('Campaign', as_index=False).agg({'Spend': 'sum', 'Sales': 'sum'}).iterrows():
            if row['Sales'] == 0 and row['Spend'] >= threshold_spesa:
                suggestions.append(f"🔴 Blocca campagna **{row['Campaign']}**: spesa €{row['Spend']:.2f} senza vendite")
            elif row['Sales'] == 0 and row['Spend'] >= 5:
                suggestions.append(f"🟠 Valuta campagna **{row['Campaign']}**: spesa €{row['Spend']:.2f} senza vendite")
            elif row['Sales'] > 0 and (row['Spend'] / row['Sales'] * 100) > acos_target:
                suggestions.append(f"🟡 Ottimizza bid in **{row['Campaign']}**: ACOS {(row['Spend'] / row['Sales'] * 100):.2f}% > target {acos_target}%")
        
        if suggestions:
            for s in suggestions: st.markdown(f"- {s}")
        else:
            st.success("Tutto sotto controllo in base ai parametri attuali.")

        # 6. TOP 3 OTTIMIZZAZIONI
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

# --- BRAND ANALYTICS (LOGICA COMPLETA) ---
def show_brand_analytics():
    st.title("📈 Brand Analytics Insights")
    with st.expander("ℹ️ Guida all'uso: Brand Analytics", expanded=False):
        st.markdown("**File richiesto:** Prestazioni delle query di ricerca (CSV).")

    brand_file = st.file_uploader("Carica il file Brand Analytics (CSV/XLSX)", type=["csv", "xlsx"])

    def norm(s: str) -> str:
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

        c_query = pick(idx, "Query di ricerca", "search_query", "Termine di ricerca", "query_di_ricerca")
        c_volume = pick(idx, "Volume query di ricerca", "search_query_volume", "volume_query_di_ricerca")
        c_imp_tot = pick(idx, "Impressioni: conteggio totale", "search_funnel_impressions_total", "Impressioni totali", "impressioni_conteggio_totale")
        c_imp_asin = pick(idx, "Impressioni: numero ASIN", "impressioni_numero_asin", "Impressioni ASIN", "impressioni_conteggio_marchio", "impressioni_conteggio_asin")
        c_clk_tot = pick(idx, "Clic: conteggio totale", "search_funnel_clicks_total", "Clic totali", "clic_conteggio_totale")
        c_clk_asin = pick(idx, "Clic: numero di ASIN", "clic_numero_asin", "Clic ASIN", "clic_conteggio_marchio", "clic_numero_di_asin")
        c_add_tot = pick(idx, "Aggiunte al carrello: conteggio totale", "search_funnel_add_to_carts_total", "aggiunte_al_carrello_conteggio_totale")
        c_add_asin = pick(idx, "Aggiunte al carrello: numero ASIN", "search_funnel_add_to_carts_brand_asin_count", "aggiunte_al_carrello_conteggio_marchio", "aggiunte_al_carrello_numero_asin")
        c_buy_tot = pick(idx, "Acquisti: conteggio totale", "search_funnel_purchases_total", "acquisti_conteggio_totale")
        c_buy_asin = pick(idx, "Acquisti: numero ASIN", "search_funnel_purchases_brand_asin_count", "acquisti_conteggio_marchio", "acquisti_numero_asin")

        if not c_query:
            st.error("Colonna 'Query di ricerca' non trovata.")
            return

        base = pd.DataFrame()
        base["Query"] = df_raw[c_query]
        base["Volume"] = pd.to_numeric(df_raw[c_volume], errors='coerce').fillna(0) if c_volume else 0
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
        out["Add To Cart Market"] = safe_div(base["ATC_tot"], base["Click_tot"])
        out["Add To Cart Asin"] = safe_div(base["ATC_asin"], base["Click_asin"])
        out["Carrelli abbandonati Market"] = safe_div(base["ATC_tot"], base["Buy_tot"])
        out["Carrelli abbandonati Asin"] = safe_div(base["ATC_asin"], base["Buy_asin"])
        out["CR Market"] = safe_div(base["Buy_tot"], base["Click_tot"])
        out["CR Asin"] = safe_div(base["Buy_asin"], base["Click_asin"])
        
        # Dashboard Totale
        sum_imp_tot = base["Impr_tot"].sum()
        sum_imp_asin = base["Impr_asin"].sum()
        sum_clk_tot = base["Click_tot"].sum()
        sum_clk_asin = base["Click_asin"].sum()
        sum_buy_tot = base["Buy_tot"].sum()
        sum_buy_asin = base["Buy_asin"].sum()

        st.subheader("Cruscotto totale")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Query analizzate", f"{len(base):,}")
        c2.metric("Volume totale", f"{int(base['Volume'].sum()):,}")
        c3.metric("Impression Share Asin", f"{safe_div(sum_imp_asin, sum_imp_tot)*100:.2f}%")
        
        st.subheader("Risultati")
        st.dataframe(out.head(50), use_container_width=True)
        download_excel({"Brand Analytics": out}, "brand_analytics.xlsx")

# --- SQP (LOGICA COMPLETA) ---
def show_sqp():
    st.title("🔎 SQP – Search Query Performance")
    with st.expander("ℹ️ Guida all'uso: SQP", expanded=False):
        st.markdown("**File richiesto:** Prestazioni query di ricerca (CSV).")

    sqp_file = st.file_uploader("Carica il file SQP (.csv)", type=["csv"])

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

        col_query = pick("Query di ricerca", "search_query", "search_term", "Termine ricerca cliente")
        col_imp_tot = pick("Impressioni: conteggio totale", "search_funnel_impressions_total", "Impressioni conteggio totale", "Impressions total")
        col_imp_brand = pick("Impressioni: conteggio marchio", "search_funnel_impressions_brand", "Impressions brand", "Impressioni conteggio marchio")
        col_clk_tot = pick("Clic: conteggio totale", "search_funnel_clicks_total", "Clicks total", "Clic conteggio totale")
        col_clk_brand = pick("Clic: conteggio marchio", "search_funnel_clicks_brand", "Clicks brand", "Clic conteggio marchio")
        col_buy_tot = pick("Acquisti: conteggio totale", "search_funnel_purchases_total", "Purchases total", "Acquisti conteggio totale")
        col_buy_brand = pick("Acquisti: conteggio marchio", "search_funnel_purchases_brand", "Purchases brand", "Acquisti conteggio marchio")

        if not col_query:
            st.error("Colonne minime non trovate.")
            return

        # Calcoli
        for c in [col_imp_tot, col_imp_brand, col_clk_tot, col_clk_brand, col_buy_tot, col_buy_brand]:
            if c: df_sqp[c] = pd.to_numeric(df_sqp[c], errors='coerce').fillna(0)

        if col_imp_tot and col_clk_tot: df_sqp["CTR MARKET"] = df_sqp[col_clk_tot] / df_sqp[col_imp_tot].replace(0, 1)
        if col_imp_brand and col_clk_brand: df_sqp["CTR MARCHIO"] = df_sqp[col_clk_brand] / df_sqp[col_imp_brand].replace(0, 1)
        if col_clk_tot and col_buy_tot: df_sqp["CR MARKET"] = df_sqp[col_buy_tot] / df_sqp[col_clk_tot].replace(0, 1)
        if col_clk_brand and col_buy_brand: df_sqp["CR MARCHIO"] = df_sqp[col_buy_brand] / df_sqp[col_clk_brand].replace(0, 1)
        
        st.subheader("📌 KPI di Sintesi")
        if col_imp_tot:
            tot_imp = df_sqp[col_imp_tot].sum()
            st.metric("Impressioni Totali", f"{int(tot_imp):,}")
        
        st.subheader("🔍 Anteprima Dati")
        st.dataframe(df_sqp.head(50), use_container_width=True)
        download_excel({"SQP": df_sqp}, "sqp_analysis.xlsx")

# --- GENERAZIONE CORRISPETTIVI ---
def show_invoices():
    st.title("📄 Generazione Corrispettivi Mensili")
    with st.expander("ℹ️ Guida all'uso: Corrispettivi", expanded=False):
        st.markdown("**File richiesto:** Report Transazioni (Transaction View).")

    file = st.file_uploader("Carica il report Transazioni con IVA (.csv)", type=["csv"])

    if file:
        df_corr = load_data_robust(file)
        if df_corr is None: return
        df_corr = clean_columns(df_corr)

        if 'TRANSACTION_TYPE' in df_corr.columns:
            df_corr = df_corr[df_corr['TRANSACTION_TYPE'].astype(str).str.upper() == 'SALE']
        
        date_col = None
        for c in df_corr.columns:
            if 'DATE' in c.upper() and 'COMPLETE' in c.upper(): date_col = c; break
        if not date_col:
            possible = [c for c in df_corr.columns if 'date' in c.lower() or 'data' in c.lower()]
            if possible: date_col = possible[0]
        
        if date_col:
            df_corr[date_col] = pd.to_datetime(df_corr[date_col], errors='coerce')
            df_corr = df_corr.dropna(subset=[date_col])
            
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

                df_group = df_corr.groupby(df_corr[date_col].dt.date).agg({col_netto: 'sum', col_iva: 'sum', col_lordo: 'sum'}).reset_index()
                df_group.columns = ['Data', 'Netto', 'IVA', 'Lordo']

                st.subheader("📊 Riepilogo Giornaliero")
                st.dataframe(df_group.style.format({'Netto': '€{:.2f}', 'IVA': '€{:.2f}', 'Lordo': '€{:.2f}'}), use_container_width=True)
                download_excel({"Riepilogo": df_group, "Dettaglio": df_corr}, "corrispettivi.xlsx")
            else:
                st.error("Colonne importi non trovate.")
        else:
            st.error("Colonna Data non trovata.")

# --- INVENTARIO FBA (LOGICA COMPLETA) ---
def show_inventory():
    st.title("📦 Controllo Inventario FBA")
    with st.expander("ℹ️ Guida all'uso: Inventario FBA", expanded=False):
        st.markdown("**File richiesto:** Mastro dell'inventario (Inventory Ledger).")

    inventory_file = st.file_uploader("Carica Inventory Ledger (CSV/XLSX)", type=["csv", "xlsx"])

    if inventory_file:
        df_inv = load_data_robust(inventory_file)
        if df_inv is None: return
        df_inv = clean_columns(df_inv)
        df_inv.columns = df_inv.columns.str.lower()

        # Check colonne
        numeric_cols = ['starting warehouse balance', 'receipts', 'customer shipments', 'customer returns', 'vendor returns', 'warehouse transfer in/out', 'found', 'lost', 'damaged', 'disposed', 'ending warehouse balance']
        for c in numeric_cols:
            if c in df_inv.columns:
                df_inv[c] = pd.to_numeric(df_inv[c], errors='coerce').fillna(0)

        if 'date' in df_inv.columns: df_inv['date'] = pd.to_datetime(df_inv['date'], errors='coerce')
        
        st.subheader("📊 KPI Globali")
        c1, c2 = st.columns(2)
        start = df_inv['starting warehouse balance'].sum() if 'starting warehouse balance' in df_inv.columns else 0
        end = df_inv['ending warehouse balance'].sum() if 'ending warehouse balance' in df_inv.columns else 0
        c1.metric("Starting Balance", f"{int(start)}")
        c2.metric("Ending Balance", f"{int(end)}")

        # Logica Anomalia (Delta) - Dal codice madre
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
                download_excel({"Anomalie": anomalies}, "reclami_fba.xlsx")
            else:
                st.success("Nessuna anomalia significativa rilevata.")

# --- FUNNEL AUDIT ---
def show_funnel_audit():
    st.title("🧭 PPC Funnel Audit")
    with st.expander("ℹ️ Guida all'uso: Funnel Audit", expanded=False):
        st.markdown("**File richiesto:** File Macro (Campagne, Spesa, Vendite).")

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
        # LOGO UFFICIALE (IMMAGINE)
        if os.path.exists("logo.png"):
            logo_b64 = get_img_as_base64("logo.png")
            if logo_b64:
                st.markdown(
                    f'<div style="text-align: left; padding-bottom: 20px;">'
                    f'<img src="data:image/png;base64,{logo_b64}" style="max-width: 100%; height: auto;">'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.error("Errore caricamento logo.png")
        else:
            st.markdown("""
            <div style='background-color: #2940A8; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;'>
                <h1 style='color: white !important; margin: 0; font-size: 40px;'>S<span style='color: #FA7838;'>Z</span></h1>
                <p style='color: white; margin: 5px 0 0 0; font-size: 10px; letter-spacing: 2px; font-weight: 600;'>SALESZONE</p>
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
