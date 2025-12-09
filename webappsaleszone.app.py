import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import unicodedata
from io import BytesIO
import os
import base64
import json
import google.generativeai as genai
import datetime

# ==============================================================================
# 1. CONFIGURAZIONE PAGINA
# ==============================================================================
st.set_page_config(
    page_title="Saleszone | Suite Operativa",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inizializzazione Session State
if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False
if 'product_library' not in st.session_state:
    st.session_state['product_library'] = []
if 'temp_library' not in st.session_state:
    st.session_state['temp_library'] = []

# ==============================================================================
# 2. STILE E BRANDING
# ==============================================================================
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
            color: #2940A8;
        }
        [data-testid="stSidebar"] {
            background-color: #F4F6FC;
            border-right: 1px solid #DBDBDB;
        }
        h1, h2, h3, h4 {
            color: #2940A8 !important;
            font-weight: 700;
        }
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
        [data-testid="stMetricValue"] {
            color: #FA7838 !important;
            font-weight: 700;
        }
        [data-testid="stMetricLabel"] {
            color: #2940A8 !important;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid #DBDBDB;
            border-radius: 8px;
        }
        .streamlit-expanderHeader {
            font-weight: 600;
            color: #2940A8;
            background-color: #F4F6FC;
            border-radius: 5px;
        }
        .stTextArea textarea {
            border: 1px solid #2940A8;
        }
        .stSuccess {
            background-color: #f0fdf4;
            color: #15803d;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 3. UTILITIES GLOBALI
# ==============================================================================
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return None

def load_product_library():
    all_products = []
    # 1. Carica da Secrets (Permanent)
    if "PRODUCT_LIBRARY_JSON" in st.secrets:
        try:
            raw_data = st.secrets["PRODUCT_LIBRARY_JSON"]
            saved_products = json.loads(raw_data)
            all_products.extend(saved_products)
        except Exception: pass

    # 2. Carica da Session State (Temporary)
    if 'temp_library' in st.session_state:
        secret_asins = [p['asin'] for p in all_products]
        for temp_p in st.session_state['temp_library']:
            if temp_p['asin'] not in secret_asins:
                all_products.append(temp_p)
    
    # 3. Filtro Privacy
    if not st.session_state['is_admin']:
        visible_products = []
        for p in all_products:
            if not p.get('private', False):
                visible_products.append(p)
        return visible_products
    return all_products

def mask_sensitive_data(df):
    if df is None or st.session_state.get('is_admin', False): return df
    hidden_list = []
    if "HIDDEN_ASINS" in st.secrets:
        hidden_list = [x.strip() for x in st.secrets["HIDDEN_ASINS"].split(",") if x.strip()]
    if not hidden_list: return df
    
    text_cols = df.select_dtypes(include=['object']).columns
    for col in text_cols:
        for secret_asin in hidden_list:
            df[col] = df[col].astype(str).str.replace(secret_asin, "******", case=False, regex=False)
    return df

def load_data_robust(file):
    """
    Funzione di caricamento potenziata:
    - Rileva automaticamente se la prima riga è metadata (es. Marchio=...)
    - Prova vari separatori (virgola, punto e virgola)
    - Prova vari encoding (utf-8, latin1)
    """
    if file is None: return None
    df = None
    try:
        # GESTIONE EXCEL
        if file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file, engine='openpyxl')
        
        # GESTIONE CSV AVANZATA
        elif file.name.endswith('.csv'):
            # Legge le prime righe come testo per capire la struttura
            content = file.getvalue().decode('utf-8', errors='ignore')
            lines = content.splitlines()
            
            # Cerca di capire dove iniziano i dati
            header_row = 0
            if len(lines) > 0:
                first_line = lines[0]
                # Se la prima riga contiene metadati Amazon tipici
                if "Marchio=" in first_line or "Periodo" in first_line:
                    header_row = 1
            
            # Reset del puntatore file
            file.seek(0)
            
            # Tentativi di lettura
            separators = [',', ';', '\t']
            encodings = ['utf-8', 'latin1']
            
            for enc in encodings:
                for sep in separators:
                    try:
                        file.seek(0)
                        temp_df = pd.read_csv(file, sep=sep, encoding=enc, header=header_row)
                        # Se ha letto più di 1 colonna, probabilmente è il formato giusto
                        if temp_df.shape[1] > 1:
                            df = temp_df
                            break
                    except:
                        continue
                if df is not None:
                    break
                    
    except Exception as e:
        st.error(f"Errore lettura file: {e}")
        return None
    
    if df is not None: 
        # Pulisce i nomi delle colonne da spazi e virgolette extra
        df.columns = [str(c).strip().replace('"', '') for c in df.columns]
        df = mask_sensitive_data(df)
        
    return df

def clean_columns(df):
    if df is not None: 
        df.columns = df.columns.str.strip().str.replace("\ufeff", "")
    return df

def download_excel(dfs_dict, filename):
    buffer = BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            for sheet_name, df in dfs_dict.items():
                df.to_excel(writer, sheet_name=str(sheet_name)[:30], index=False)
        st.download_button(label=f"📥 Scarica {filename}", data=buffer.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e: st.error(f"Errore download: {e}")

# ==============================================================================
# 4. MODULI APPLICAZIONE
# ==============================================================================

# --- LIBRERIA PRODOTTI ---
def show_product_library():
    st.title("📚 Libreria Prodotti")
    
    if st.session_state['is_admin']:
        st.info("🔓 Modalità Admin Attiva")
        
        with st.expander("➕ Aggiungi/Modifica Prodotto", expanded=False):
            c1, c2, c3 = st.columns([2, 2, 1])
            new_brand = c1.text_input("Brand")
            new_asin = c2.text_input("ASIN")
            is_private = c3.checkbox("Privato", value=False)
            new_name = st.text_input("Nome Prodotto (Alias)")
            new_context = st.text_area("Contenuto Pagina Prodotto (Prompt AI)", height=150)
            
            if st.button("Salva in Sessione"):
                if new_asin and new_name:
                    st.session_state['temp_library'].append({
                        "brand": new_brand, "asin": new_asin, "name": new_name,
                        "context": new_context, "private": is_private
                    })
                    st.success(f"Prodotto aggiunto! Per renderlo permanente, copia il JSON nei Secrets.")
                    st.rerun()
                else: st.warning("ASIN e Nome obbligatori.")

        full_library = load_product_library()
        if full_library:
            with st.expander("💾 Codice JSON per Secrets", expanded=True):
                st.markdown("Copia questo codice nei Secrets assegnandolo a `PRODUCT_LIBRARY_JSON`.")
                json_str = json.dumps(full_library, indent=2)
                st.code(json_str, language='json')

    st.divider()
    st.subheader("Elenco Prodotti")
    products = load_product_library()
    
    if not products:
        st.info("La libreria è vuota.")
    else:
        all_brands = sorted(list(set([p['brand'] for p in products if p['brand']])))
        sel_brand = st.selectbox("Filtra per Brand", ["Tutti"] + all_brands)
        filtered_prods = [p for p in products if sel_brand == "Tutti" or p['brand'] == sel_brand]
        
        display_data = []
        for p in filtered_prods:
            display_data.append({
                "Brand": p['brand'], "ASIN": p['asin'], "Nome": p['name'],
                "Visibilità": "🔒 Privato" if p.get('private') else "🌍 Pubblico"
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True)

# --- HOME ---
def show_home():
    col1, col2 = st.columns([1, 2])
    with col1:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        else: st.markdown("""<div style='background-color: #2940A8; padding: 30px; border-radius: 15px; text-align: center;'><h1 style='color: white !important; margin: 0; font-size: 60px;'>S<span style='color: #FA7838;'>Z</span></h1></div>""", unsafe_allow_html=True)
            
    with col2:
        st.title("Benvenuto in Saleszone")
        st.markdown("### Il tuo spazio di crescita su Amazon.")
        st.write("Questa suite operativa integra tutti gli strumenti necessari per l'analisi e l'ottimizzazione.")
        products = load_product_library()
        st.metric("Prodotti in Libreria", len(products))
    
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1: st.info("🎯 **Missione**\n\nSupportare i brand con consulenza strategica.")
    with c2: st.success("💎 **Valori**\n\nProfessionalità, Autenticità, Trasparenza.")
    with c3: st.warning("🤝 **Metodo**\n\nNessun intermediario, solo risultati.")

# --- PPC OPTIMIZER ---
def show_ppc_optimizer():
    st.title("📊 Saleszone Ads Optimizer")
    with st.expander("ℹ️ Guida all'uso", expanded=False): st.markdown("**File richiesto:** Report Termini di Ricerca.")

    col1, col2 = st.columns(2)
    with col1: search_term_file = st.file_uploader("Report Search Term", type=["csv", "xlsx"])
    with col2: placement_file = st.file_uploader("Report Placement", type=["csv", "xlsx"])

    c1, c2, c3 = st.columns(3)
    acos_target = c1.number_input("🎯 ACOS Target (%)", 30)
    click_min = c2.number_input("⚠️ Click min (no vendite)", 10)
    percent_threshold = c3.number_input("📊 % Spesa critica", 10)

    if search_term_file:
        df = load_data_robust(search_term_file)
        if df is None: return
        df = clean_columns(df)

        mapping = {
            'Nome portafoglio': 'Portfolio', 'Portfolio name': 'Portfolio',
            'Nome campagna': 'Campaign', 'Campaign Name': 'Campaign',
            'Targeting': 'Keyword', 'Termine ricerca cliente': 'Search Term', 'Customer Search Term': 'Search Term',
            'Impressioni': 'Impressions', 'Impressions': 'Impressions', 'Clic': 'Clicks', 'Clicks': 'Clicks',
            'Spesa': 'Spend', 'Spend': 'Spend', 'Costo': 'Spend', 'Vendite totali (€) 7 giorni': 'Sales', 
            '7 Day Total Sales': 'Sales', 'Vendite': 'Sales', 'Totale ordini (#) 7 giorni': 'Orders', 
            '7 Day Total Orders': 'Orders', 'Ordini': 'Orders'
        }
        df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)

        req = ['Impressions', 'Clicks', 'Spend', 'Sales', 'Orders']
        for col in req:
            if col not in df.columns: df[col] = 0
            else:
                if df[col].dtype == object: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
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
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Spesa Totale", f"€{tot_sp:,.2f}")
        k2.metric("Vendite Totali", f"€{tot_sa:,.2f}")
        k3.metric("ACOS Medio", f"{avg_ac:.2f}%")
        k4.metric("CTR Totale", f"{(df['Clicks'].sum()/df['Impressions'].sum()*100):.2f}%")

        st.subheader("📦 Panoramica per Portafoglio")
        pf_grp = df.groupby('Portfolio', as_index=False).agg({'Impressions': 'sum', 'Clicks': 'sum', 'Spend': 'sum', 'Sales': 'sum', 'Orders': 'sum'})
        pf_grp['ACOS'] = pf_grp.apply(lambda r: (r['Spend']/r['Sales']*100) if r['Sales']>0 else 0, axis=1)
        st.dataframe(pf_grp.style.format({'Spend': '€{:.2f}', 'Sales': '€{:.2f}', 'ACOS': '{:.2f}%'}), use_container_width=True)

        st.subheader("📊 Panoramica per Campagna")
        p_opts = ["Tutti"] + sorted(df['Portfolio'].unique().tolist())
        sel_p = st.selectbox("Filtra Portafoglio", p_opts)
        df_c = df[df['Portfolio'] == sel_p] if sel_p != "Tutti" else df
        cp_grp = df_c.groupby('Campaign', as_index=False).agg({'Impressions': 'sum', 'Clicks': 'sum', 'Spend': 'sum', 'Sales': 'sum', 'Orders': 'sum'})
        cp_grp['ACOS'] = cp_grp.apply(lambda r: (r['Spend']/r['Sales']*100) if r['Sales']>0 else 0, axis=1)
        st.dataframe(cp_grp.style.format({'Spend': '€{:.2f}', 'Sales': '€{:.2f}', 'ACOS': '{:.2f}%'}), use_container_width=True)

        st.subheader("🔍 Dettaglio Search Terms")
        c1, c2 = st.columns(2)
        sel_camp = c1.selectbox("Filtra Campagna", ["Tutte"] + sorted(df['Campaign'].unique().tolist()))
        df_terms = df[df['Campaign'] == sel_camp] if sel_camp != "Tutte" else df
        waste_terms = df_terms[(df_terms['Sales'] == 0) & (df_terms['Clicks'] >= click_min)].sort_values(by='Spend', ascending=False)
        st.dataframe(waste_terms[['Campaign', 'Search Term', 'Clicks', 'Spend']].style.format({'Spend': '€{:.2f}'}), use_container_width=True)

        # INTEGRAZIONE AI
        st.markdown("---")
        st.subheader("🤖 Analisi AI (Gemini)")
        
        api_key = None
        if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
        else: api_key = st.session_state.get('gemini_api_key', '')
        
        if not api_key:
            st.warning("⚠️ Inserisci API Key Gemini nella sidebar.")
        elif not waste_terms.empty:
            st.markdown("Analisi termini senza vendite.")
            sel_camp_ai = st.selectbox("Campagna da analizzare", sorted(waste_terms['Campaign'].unique().tolist()))
            target_waste = waste_terms[waste_terms['Campaign'] == sel_camp_ai]
            st.info(f"Trovati **{len(target_waste)}** termini da analizzare.")
            
            use_lib = st.checkbox("Usa prodotto da Libreria", value=True)
            prod_ctx = ""
            
            if use_lib:
                products = load_product_library()
                if products:
                    opts = [f"{p['brand']} - {p['name']} ({p['asin']})" for p in products]
                    sel_prod = st.selectbox("Scegli Prodotto", opts)
                    if sel_prod:
                        asin = sel_prod.split("(")[-1].replace(")", "")
                        p_obj = next((p for p in products if p['asin'] == asin), None)
                        if p_obj: prod_ctx = p_obj['context']
                else: st.warning("Libreria vuota.")
            else:
                prod_ctx = st.text_area("Incolla testo pagina prodotto:", height=100)
            
            if st.button("✨ Analizza con Gemini"):
                if not prod_ctx: st.error("Manca il contesto prodotto.")
                else:
                    with st.spinner("Analisi in corso..."):
                        try:
                            genai.configure(api_key=api_key)
                            model = genai.GenerativeModel('gemini-pro')
                            t_list = target_waste['Search Term'].head(150).tolist()
                            prompt = f"""
                            Analizza i seguenti termini (Senza vendite) per la campagna '{sel_camp_ai}'.
                            Termini: {', '.join(t_list)}
                            Contesto Prodotto: {prod_ctx}
                            Task: Identifica Negative Exact. 3 gruppi (Incoerenti, Affini ma no ordini). Lista pulita.
                            """
                            resp = model.generate_content(prompt)
                            st.markdown(resp.text)
                        except Exception as e: st.error(f"Errore AI: {e}")

# --- BRAND ANALYTICS ---
def show_brand_analytics():
    st.title("📈 Brand Analytics")
    with st.expander("ℹ️ Guida", expanded=False): st.markdown("**File:** Prestazioni query di ricerca (CSV).")
    f = st.file_uploader("Carica File", type=["csv", "xlsx"])
    if f:
        df = load_data_robust(f)
        if df is None: return
        df = clean_columns(df)
        
        # Mappatura case-insensitive
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
        a_tot = pk("Aggiunte al carrello: conteggio totale", "search_funnel_add_to_carts_total")
        a_br = pk("Aggiunte al carrello: numero ASIN", "search_funnel_add_to_carts_brand_asin_count", "aggiunte_al_carrello_conteggio_marchio")
        b_tot = pk("Acquisti: conteggio totale", "search_funnel_purchases_total")
        b_br = pk("Acquisti: numero ASIN", "search_funnel_purchases_brand_asin_count", "acquisti_conteggio_marchio")

        if not q: 
            st.error("Colonne non trovate.")
            return

        out = pd.DataFrame()
        out["Query"] = df[q]
        out["Volume"] = df[vol] if vol else 0
        def safe(c): return pd.to_numeric(df[c], errors='coerce').fillna(0) if c else 0
        
        out["Impr Share"] = (safe(i_br) / safe(i_tot).replace(0, 1) * 100)
        out["Click Share"] = (safe(c_br) / safe(c_tot).replace(0, 1) * 100)
        out["CTR Market"] = safe(c_tot) / safe(i_tot).replace(0, 1)
        out["CTR Asin"] = safe(c_br) / safe(i_br).replace(0, 1)
        out["ATC Market"] = safe(a_tot) / safe(c_tot).replace(0, 1)
        out["ATC Asin"] = safe(a_br) / safe(c_br).replace(0, 1)
        out["CR Market"] = safe(b_tot) / safe(c_tot).replace(0, 1)
        out["CR Asin"] = safe(b_br) / safe(c_br).replace(0, 1)
        
        st.dataframe(out.head(50), use_container_width=True)
        download_excel({"Brand Analytics": out}, "brand_analytics.xlsx")

# --- SQP ---
def show_sqp():
    st.title("🔎 SQP Analysis")
    with st.expander("ℹ️ Guida", expanded=False): st.markdown("**File:** Prestazioni query di ricerca (CSV).")
    f = st.file_uploader("Carica File", type=["csv"])
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

        q = pk("Query di ricerca", "search_query", "termine_di_ricerca")
        i_tot = pk("Impressioni_conteggio_totale", "impressions_total", "impressioni_conteggio_totale")
        i_br = pk("Impressioni_conteggio_marchio", "impressions_brand")
        c_tot = pk("Clic_conteggio_totale", "clicks_total", "clic_conteggio_totale")
        c_br = pk("Clic_conteggio_marchio", "clicks_brand", "clic_conteggio_marchio")
        b_tot = pk("Acquisti_conteggio_totale", "purchases_total", "acquisti_conteggio_totale")
        b_br = pk("Acquisti_conteggio_marchio", "purchases_brand", "acquisti_conteggio_marchio")

        if not q: st.error("Colonne non trovate."); return
        def safe(c): return pd.to_numeric(df[c], errors='coerce').fillna(0) if c else 0

        df["CTR MARKET"] = safe(c_tot) / safe(i_tot).replace(0, 1)
        df["CTR MARCHIO"] = safe(c_br) / safe(i_br).replace(0, 1)
        df["CR MARKET"] = safe(b_tot) / safe(c_tot).replace(0, 1)
        df["CR MARCHIO"] = safe(b_br) / safe(c_br).replace(0, 1)
        
        st.metric("CTR Medio Market", f"{df['CTR MARKET'].mean()*100:.2f}%")
        st.dataframe(df.head(50), use_container_width=True)
        download_excel({"SQP": df}, "sqp_analysis.xlsx")

# --- INVENTARIO ---
def show_inventory():
    st.title("📦 Inventario FBA")
    with st.expander("ℹ️ Guida", expanded=False): st.markdown("**File:** Inventory Ledger.")
    f = st.file_uploader("Carica File", type=["csv", "xlsx"])
    if f:
        df = load_data_robust(f)
        if df is None: return
        df = clean_columns(df)
        df.columns = df.columns.str.lower()
        
        # Logica Delta
        if 'ending warehouse balance' in df.columns:
            inc = df[['receipts', 'customer returns', 'found']].sum(axis=1) if 'receipts' in df.columns else 0
            dec = df[['customer shipments', 'lost', 'damaged', 'disposed']].sum(axis=1).abs() if 'lost' in df.columns else 0
            df['ending_teorico'] = df.get('starting warehouse balance', 0) + inc - dec
            df['delta'] = df['ending warehouse balance'] - df['ending_teorico']
            anomalies = df[df['delta'].abs() > 0.1].copy()
            if not anomalies.empty:
                st.warning(f"Rilevate {len(anomalies)} anomalie.")
                st.dataframe(anomalies)
                download_excel({"Anomalie": anomalies}, "reclami.xlsx")
            else: st.success("Nessuna anomalia.")
            
        # Logica Damaged
        if 'damaged' in df.columns and 'transaction type' in df.columns:
             damaged_transfer = df[
                (df['transaction type'].astype(str).str.lower().str.contains('adjustment')) & 
                (df['disposition'].isin(['damaged'])) &
                (df['damaged'] > 0)
            ].copy()
             if not damaged_transfer.empty:
                st.subheader("📦 Unità Danneggiate (Adjustment)")
                st.dataframe(damaged_transfer)

# --- FUNNEL AUDIT ---
def show_funnel_audit():
    st.title("🧭 Funnel Audit")
    with st.expander("ℹ️ Guida", expanded=False): st.markdown("**File:** Macro Campagne.")
    f = st.file_uploader("Carica File", type=["xlsx", "csv"])
    if f:
        df = load_data_robust(f)
        if df is None: return
        df = clean_columns(df)
        def pick(df, candidates):
            for c in candidates:
                for col in df.columns: 
                    if c.lower() in col.lower(): return col
            return None
        
        c_n = pick(df, ["Campagne", "Campaign"])
        c_s = pick(df, ["Spesa", "Spend"])
        c_v = pick(df, ["Vendite", "Sales"])
        
        if c_n and c_s:
            df['Spend'] = pd.to_numeric(df[c_s].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
            df['Sales'] = pd.to_numeric(df[c_v].astype(str).str.replace(',','.'), errors='coerce').fillna(0) if c_v else 0
            
            def get_layer(n):
                n = str(n).upper()
                if "BRAND" in n or "DEFENSE" in n: return "BOFU (Brand)"
                if "GENERIC" in n or "BROAD" in n: return "TOFU (Discovery)"
                return "MOFU (Competitor)"
            
            df['Layer'] = df[c_n].apply(get_layer)
            kpi = df.groupby('Layer')[['Spend', 'Sales']].sum().reset_index()
            st.bar_chart(kpi.set_index('Layer')['Spend'])
            st.dataframe(kpi)

# --- CORRISPETTIVI ---
def show_invoices():
    st.title("📄 Corrispettivi")
    with st.expander("ℹ️ Guida", expanded=False): st.markdown("**File:** Report Transazioni.")
    f = st.file_uploader("Carica File", type=["csv"])
    if f:
        df = load_data_robust(f)
        if df is None: return
        df = clean_columns(df)
        
        if 'TRANSACTION_TYPE' in df.columns:
            df = df[df['TRANSACTION_TYPE'].astype(str).str.upper() == 'SALE']

        date_col = None
        for c in df.columns:
            if 'DATE' in c.upper() and 'COMPLETE' in c.upper(): date_col = c; break
        
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            cols_amt = [c for c in df.columns if 'VALUE' in c]
            if cols_amt:
                for c in cols_amt: df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                grp = df.groupby(df[date_col].dt.date)[cols_amt].sum().reset_index()
                st.dataframe(grp, use_container_width=True)
                download_excel({"Corrispettivi": grp}, "corrispettivi.xlsx")
            else: st.error("Colonne importi non trovate.")
        else: st.error("Colonna data non trovata.")

# ==============================================================================
# 5. MAIN NAVIGATOR
# ==============================================================================
def main():
    with st.sidebar:
        # LOGO
        if os.path.exists("logo.png"):
            b64 = get_img_as_base64("logo.png")
            st.markdown(f'<img src="data:image/png;base64,{b64}" style="max-width:100%">', unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='color:#2940A8'>S<span style='color:#FA7838'>Z</span> SALESZONE</h1>", unsafe_allow_html=True)
        
        # API KEY
        if "GEMINI_API_KEY" in st.secrets:
            st.session_state['gemini_api_key'] = st.secrets["GEMINI_API_KEY"]
            st.success("✅ AI Attiva")
        else:
            k = st.text_input("Gemini API Key", type="password")
            if k: st.session_state['gemini_api_key'] = k
        
        # ADMIN LOGIN
        with st.expander("Admin Area"):
            pwd = st.text_input("Password", type="password")
            if st.button("Login"):
                if "ADMIN_PASSWORD" in st.secrets and pwd == st.secrets["ADMIN_PASSWORD"]:
                    st.session_state['is_admin'] = True
                    st.success("Login OK")
                    st.rerun()
                else: st.error("Errore")
        
        if st.session_state.get('is_admin'):
            if st.button("Logout"): 
                st.session_state['is_admin'] = False
                st.rerun()

        st.markdown("---")
        MENU = ["Home", "Libreria Prodotti", "PPC Optimizer", "Brand Analytics Insights", "SQP Analysis", "Generazione Corrispettivi", "Controllo Inventario FBA", "Funnel Audit"]
        sel = st.radio("Menu", MENU, label_visibility="collapsed")
        st.caption("© 2025 Saleszone Agency")

    if sel == "Home": show_home()
    elif sel == "Libreria Prodotti": show_product_library()
    elif sel == "PPC Optimizer": show_ppc_optimizer()
    elif sel == "Brand Analytics Insights": show_brand_analytics()
    elif sel == "SQP Analysis": show_sqp()
    elif sel == "Generazione Corrispettivi": show_invoices()
    elif sel == "Controllo Inventario FBA": show_inventory()
    elif sel == "Funnel Audit": show_funnel_audit()

if __name__ == "__main__":
    main()
