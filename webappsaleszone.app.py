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
# 3. UTILITIES GLOBALI
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
    """Caricamento file CSV/Excel robusto."""
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

# ==============================================================================
# 4. MODULI APPLICAZIONE
# ==============================================================================

# --- HOME ---
def show_home():
    col1, col2 = st.columns([1, 2])
    with col1:
        # Logo in home page
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
        else:
            st.warning("⚠️ Carica il file 'logo.png' su GitHub per vederlo qui.")
            
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

    st.subheader("📂 Carica i tuoi report")
    col1, col2 = st.columns(2)
    with col1:
        search_term_file = st.file_uploader("Carica Report Search Term (Obbligatorio)", type=["csv", "xlsx"])
    with col2:
        placement_file = st.file_uploader("Carica Report Placement (Opzionale)", type=["csv", "xlsx"])

    c1, c2, c3 = st.columns(3)
    acos_target = c1.number_input("🎯 ACOS Target (%)", min_value=1, max_value=100, value=30)
    click_min = c2.number_input("⚠️ Click minimo per Search Terms senza vendite", min_value=1, value=10)
    percent_threshold = c3.number_input("📊 % Spesa per segnalazione critica", min_value=1, max_value=100, value=10)

    if search_term_file:
        df = load_data_robust(search_term_file)
        if df is None: return
        df = clean_columns(df)

        mapping = {
            'Nome portafoglio': 'Portfolio', 'Portfolio name': 'Portfolio',
            'Nome campagna': 'Campaign', 'Campaign Name': 'Campaign',
            'Targeting': 'Keyword', 'Termine ricerca cliente': 'Search Term', 'Customer Search Term': 'Search Term',
            'Impressioni': 'Impressions', 'Impressions': 'Impressions',
            'Clic': 'Clicks', 'Clicks': 'Clicks',
            'Spesa': 'Spend', 'Spend': 'Spend', 'Costo': 'Spend',
            'Vendite totali (€) 7 giorni': 'Sales', '7 Day Total Sales': 'Sales', 'Vendite': 'Sales',
            'Totale ordini (#) 7 giorni': 'Orders', '7 Day Total Orders': 'Orders', 'Ordini': 'Orders'
        }
        df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)

        req = ['Impressions', 'Clicks', 'Spend', 'Sales', 'Orders']
        for col in req:
            if col not in df.columns: df[col] = 0
            else:
                if df[col].dtype == object:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                else: df[col] = df[col].fillna(0)

        if 'Portfolio' not in df.columns: df['Portfolio'] = 'N/A'
        if 'Campaign' not in df.columns: df['Campaign'] = 'Sconosciuta'
        df['Portfolio'].fillna('Nessun Portafoglio', inplace=True)

        df['CPC'] = df['Spend'] / df['Clicks'].replace(0, 1)
        df['CTR'] = (df['Clicks'] / df['Impressions'].replace(0, 1)) * 100
        df['CR'] = (df['Orders'] / df['Clicks'].replace(0, 1)) * 100
        df['ACOS'] = df.apply(lambda r: (r['Spend'] / r['Sales'] * 100) if r['Sales'] > 0 else None, axis=1)

        tot_sp = df['Spend'].sum()
        tot_sa = df['Sales'].sum()
        avg_ac = (tot_sp / tot_sa * 100) if tot_sa > 0 else 0
        
        st.markdown("### 📌 KPI Principali")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Spesa Totale", f"€{tot_sp:,.2f}")
        k2.metric("Vendite Totali", f"€{tot_sa:,.2f}")
        k3.metric("ACOS Medio", f"{avg_ac:.2f}%")
        k4.metric("CTR Totale", f"{(df['Clicks'].sum()/df['Impressions'].sum()*100):.2f}%")
        k5.metric("CR Totale", f"{(df['Orders'].sum()/df['Clicks'].sum()*100):.2f}%")

        st.subheader("📦 Panoramica per Portafoglio")
        pf_grp = df.groupby('Portfolio', as_index=False).agg({
            'Impressions': 'sum', 'Clicks': 'sum', 'Spend': 'sum', 'Sales': 'sum', 'Orders': 'sum'
        })
        pf_grp['ACOS'] = pf_grp.apply(lambda r: (r['Spend']/r['Sales']*100) if r['Sales']>0 else 0, axis=1)
        st.dataframe(pf_grp.style.format({'Spend': '€{:.2f}', 'Sales': '€{:.2f}', 'ACOS': '{:.2f}%'}), use_container_width=True)

        st.subheader("📊 Panoramica per Campagna")
        p_opt = ["Tutti"] + sorted(df['Portfolio'].unique().tolist())
        sel_p = st.selectbox("Filtra per Portafoglio", p_opt)
        df_c = df[df['Portfolio'] == sel_p] if sel_p != "Tutti" else df
        
        cp_grp = df_c.groupby('Campaign', as_index=False).agg({
            'Impressions': 'sum', 'Clicks': 'sum', 'Spend': 'sum', 'Sales': 'sum', 'Orders': 'sum'
        })
        cp_grp['ACOS'] = cp_grp.apply(lambda r: (r['Spend']/r['Sales']*100) if r['Sales']>0 else 0, axis=1)
        st.dataframe(cp_grp.style.format({'Spend': '€{:.2f}', 'Sales': '€{:.2f}', 'ACOS': '{:.2f}%'}), use_container_width=True)

        st.subheader("🔍 Dettaglio Search Terms")
        waste = df[(df['Sales'] == 0) & (df['Clicks'] >= click_min)].sort_values('Spend', ascending=False)
        st.dataframe(waste[['Campaign', 'Search Term', 'Clicks', 'Spend']].style.format({'Spend': '€{:.2f}'}), use_container_width=True)

        st.subheader("🤖 Suggerimenti AI")
        thr = tot_sp * (percent_threshold/100)
        for _, r in cp_grp.iterrows():
            if r['Sales'] == 0 and r['Spend'] >= thr:
                st.error(f"🔴 Blocca campagna **{r['Campaign']}**: spesa €{r['Spend']:.2f} senza vendite")
            elif r['Sales'] > 0 and r['ACOS'] > acos_target:
                st.warning(f"🟡 Ottimizza **{r['Campaign']}**: ACOS {r['ACOS']:.2f}%")

# --- BRAND ANALYTICS ---
def show_brand_analytics():
    st.title("📈 Brand Analytics")
    f = st.file_uploader("Carica Brand Analytics (CSV/XLSX)", type=["csv", "xlsx"])
    if f:
        df = load_data_robust(f)
        if df is None: return
        df = clean_columns(df)
        
        # Logica di mappatura robusta
        norm = lambda x: str(x).lower().strip().replace(" ", "_")
        cols = {norm(c): c for c in df.columns}
        
        def pk(*a): 
            for x in a: 
                if norm(x) in cols: return cols[norm(x)]
            return None

        q = pk("Query di ricerca", "search_query", "Termine di ricerca")
        vol = pk("Volume query di ricerca", "search_query_volume")
        i_tot = pk("Impressioni: conteggio totale", "search_funnel_impressions_total")
        i_br = pk("Impressioni: numero ASIN", "impressioni_numero_asin", "impressioni_conteggio_marchio")
        c_tot = pk("Clic: conteggio totale", "search_funnel_clicks_total")
        c_br = pk("Clic: numero di ASIN", "clic_numero_asin", "clic_conteggio_marchio")
        
        if not q: 
            st.error("Colonne non riconosciute.")
            return

        out = pd.DataFrame()
        out["Query"] = df[q]
        out["Volume"] = df[vol] if vol else 0
        
        def safe(c): return pd.to_numeric(df[c], errors='coerce').fillna(0) if c else 0
        
        out["Impr Share"] = (safe(i_br) / safe(i_tot).replace(0, 1) * 100)
        out["Click Share"] = (safe(c_br) / safe(c_tot).replace(0, 1) * 100)
        
        st.dataframe(out.head(50), use_container_width=True)

# --- SQP ---
def show_sqp():
    st.title("🔎 Search Query Performance")
    f = st.file_uploader("Carica SQP (.csv)", type=["csv"])
    if f:
        df = load_data_robust(f)
        if df is None: return
        df = clean_columns(df)
        
        norm = lambda x: str(x).lower().strip().replace(":", "").replace(" ", "_")
        cols = {norm(c): c for c in df.columns}
        def pk(*a): 
            for x in a: 
                if norm(x) in cols: return cols[norm(x)]
            return None

        # Mappatura
        q = pk("Query di ricerca", "search_query")
        i_tot = pk("Impressioni_conteggio_totale", "impressions_total")
        i_br = pk("Impressioni_conteggio_marchio", "impressions_brand")
        c_tot = pk("Clic_conteggio_totale", "clicks_total")
        c_br = pk("Clic_conteggio_marchio", "clicks_brand")
        b_tot = pk("Acquisti_conteggio_totale", "purchases_total")
        b_br = pk("Acquisti_conteggio_marchio", "purchases_brand")

        if not q:
            st.error("Colonne SQP non trovate.")
            return

        def safe(c): return pd.to_numeric(df[c], errors='coerce').fillna(0) if c else 0

        df["CTR MARKET"] = safe(c_tot) / safe(i_tot).replace(0, 1)
        df["CTR MARCHIO"] = safe(c_br) / safe(i_br).replace(0, 1)
        df["CR MARKET"] = safe(b_tot) / safe(c_tot).replace(0, 1)
        df["CR MARCHIO"] = safe(b_br) / safe(c_br).replace(0, 1)

        st.subheader("KPI Calcolati")
        c1, c2 = st.columns(2)
        c1.metric("CTR Medio Market", f"{df['CTR MARKET'].mean()*100:.2f}%")
        c2.metric("CR Medio Market", f"{df['CR MARKET'].mean()*100:.2f}%")
        
        st.dataframe(df.head(50), use_container_width=True)

# --- INVENTARIO FBA ---
def show_inventory():
    st.title("📦 Controllo Inventario FBA")
    f = st.file_uploader("Inventory Ledger", type=["csv", "xlsx"])
    if f:
        df = load_data_robust(f)
        if df is None: return
        df.columns = df.columns.str.lower()
        
        # Logica
        lost = df[df['transaction type'].astype(str).str.lower().str.contains('adjustment') & df['disposition'].isin(['lost', 'damaged'])] if 'transaction type' in df.columns else pd.DataFrame()
        
        if not lost.empty:
            st.write("Unità perse/danneggiate rilevate:")
            st.dataframe(lost)
        else:
            st.success("Nessuna discrepanza evidente.")

# --- ALTRE FUNZIONI ---
def show_funnel_audit():
    st.title("🧭 PPC Funnel Audit")
    st.info("Carica il file Macro.")
    f = st.file_uploader("File Macro", type=["xlsx", "csv"])
    if f: st.write("File caricato.")

def show_invoices():
    st.title("📄 Corrispettivi")
    st.info("Carica il report Transazioni.")
    f = st.file_uploader("File Transazioni", type=["csv"])
    if f: st.write("File caricato.")

# ==============================================================================
# 5. MAIN NAVIGATOR
# ==============================================================================
def main():
    with st.sidebar:
        # LOGO UFFICIALE (IMMAGINE)
        # Usiamo HTML con max-width: 100% per evitare che venga tagliato
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
            # Fallback testuale se l'utente non ha ancora caricato l'immagine
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
