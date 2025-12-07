import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import unicodedata
from io import BytesIO
import os
import base64
import google.generativeai as genai

# Firebase Imports (se li userai in futuro, altrimenti li lasciamo commentati per evitare errori se non configurati)
# from firebase_admin import credentials, firestore, initialize_app, get_app

# ==============================================================================
# 1. CONFIGURAZIONE PAGINA
# ==============================================================================
st.set_page_config(
    page_title="Saleszone | Suite Operativa",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inizializzazione Session State per la Libreria Prodotti (Memoria temporanea)
if 'product_library' not in st.session_state:
    st.session_state['product_library'] = [] 

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
        /* Text Area */
        .stTextArea textarea {
            border: 1px solid #2940A8;
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
    except:
        return None

def load_data_robust(file):
    if file is None: return None
    
    if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
        try:
            return pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            st.error(f"Errore lettura Excel: {e}")
            return None

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
# 4. MODULI APPLICAZIONE
# ==============================================================================

# --- LIBRERIA PRODOTTI ---
def show_product_library():
    st.title("📚 Libreria Prodotti (ASIN)")
    st.write("Gestisci qui i tuoi prodotti per velocizzare l'analisi AI.")

    with st.expander("➕ Aggiungi Nuovo Prodotto", expanded=True):
        c1, c2 = st.columns(2)
        new_brand = c1.text_input("Brand")
        new_asin = c2.text_input("ASIN")
        new_name = st.text_input("Nome Prodotto (Alias)")
        new_context = st.text_area("Contenuto Pagina Prodotto (Titolo, Bullet Points, Descrizione)", height=150, help="Questo testo verrà passato all'IA come contesto.")
        
        if st.button("Salva Prodotto"):
            if new_asin and new_name:
                exists = any(p['asin'] == new_asin for p in st.session_state['product_library'])
                if exists:
                    st.error(f"L'ASIN {new_asin} esiste già nella libreria.")
                else:
                    st.session_state['product_library'].append({
                        "brand": new_brand,
                        "asin": new_asin,
                        "name": new_name,
                        "context": new_context
                    })
                    st.success(f"Prodotto **{new_name}** aggiunto con successo!")
            else:
                st.warning("Compila almeno ASIN e Nome Prodotto.")

    st.divider()
    st.subheader("📦 I tuoi prodotti salvati")
    
    if not st.session_state['product_library']:
        st.info("La libreria è vuota. Aggiungi il primo prodotto sopra.")
    else:
        c_filter1, c_filter2 = st.columns(2)
        brands = sorted(list(set([p['brand'] for p in st.session_state['product_library'] if p['brand']])))
        filter_brand = c_filter1.selectbox("Filtra per Brand", ["Tutti"] + brands)
        
        display_list = st.session_state['product_library']
        if filter_brand != "Tutti":
            display_list = [p for p in display_list if p['brand'] == filter_brand]
        
        if display_list:
            df_lib = pd.DataFrame(display_list)
            st.dataframe(df_lib[['brand', 'asin', 'name']], use_container_width=True)
            
            to_delete = st.selectbox("Seleziona un prodotto da ELIMINARE", ["-- Nessuno --"] + [f"{p['asin']} - {p['name']}" for p in display_list])
            if to_delete != "-- Nessuno --":
                if st.button("🗑️ Elimina selezionato"):
                    asin_del = to_delete.split(" - ")[0]
                    st.session_state['product_library'] = [p for p in st.session_state['product_library'] if p['asin'] != asin_del]
                    st.rerun()

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
        Questa suite operativa integra tutti gli strumenti necessari per l'analisi e l'ottimizzazione 
        del tuo account Amazon Seller. 
        """)
        
        prod_count = len(st.session_state['product_library'])
        st.metric("Prodotti in Libreria", prod_count)
    
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
    
    with st.expander("ℹ️ Guida all'uso: PPC Optimizer", expanded=False):
        st.markdown("""
        **File richiesto:** Report Termini di Ricerca (Sponsored Products).
        **Analisi:** KPI, Portafogli, Campagne, Sprechi, Suggerimenti AI.
        """)

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
            'Targeting': 'Keyword', 
            'Termine ricerca cliente': 'Search Term', 'Customer Search Term': 'Search Term',
            'Impressioni': 'Impressions', 'Impressions': 'Impressions',
            'Clic': 'Clicks', 'Clicks': 'Clicks',
            'Spesa': 'Spend', 'Spend': 'Spend', 'Costo': 'Spend',
            'Vendite totali (€) 7 giorni': 'Sales', '7 Day Total Sales': 'Sales', 'Vendite': 'Sales',
            'Totale ordini (#) 7 giorni': 'Orders', '7 Day Total Orders': 'Orders', 'Ordini': 'Orders'
        }
        df.rename(columns={k: v for k, v in mapping.items() if k in df.columns}, inplace=True)

        required_cols = ['Impressions', 'Clicks', 'Spend', 'Sales', 'Orders']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0
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

        st.subheader(f"⚠️ Search Terms senza vendite (>{click_min} click)")
        waste_terms = df[(df['Sales'] == 0) & (df['Clicks'] >= click_min)].sort_values(by='Spend', ascending=False)
        st.dataframe(waste_terms[['Portfolio', 'Search Term', 'Keyword', 'Campaign', 'Clicks', 'Spend']].style.format({'Spend': '€{:.2f}'}), use_container_width=True)

        # 5. INTEGRAZIONE AI (GEMINI) - CON LIBRERIA ASIN E SECRETS
        st.markdown("---")
        st.subheader("🤖 Analisi AI Termini Negativi (Gemini)")
        
        # LOGICA GESTIONE API KEY (SECRETS + INPUT)
        api_key = None
        
        # 1. Cerca nei secrets (priorità)
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ Gemini API Key caricata dalle impostazioni (Secrets).")
        # 2. Cerca nella sessione o input manuale
        else:
            api_key = st.session_state.get('gemini_api_key', '')
            if not api_key:
                st.warning("⚠️ Chiave non trovata nei Secrets. Inseriscila nella sidebar per usare l'AI.")
        
        if api_key:
            if not waste_terms.empty:
                st.markdown("Seleziona una campagna specifica per analizzare i suoi termini inefficienti con l'IA.")
                
                # A. Seleziona Campagna
                waste_campaigns = sorted(waste_terms['Campaign'].unique().tolist())
                selected_campaign_ai = st.selectbox("Seleziona la Campagna da analizzare", waste_campaigns, key="ai_campaign_select")
                
                target_waste_terms = waste_terms[waste_terms['Campaign'] == selected_campaign_ai]
                st.info(f"Trovati **{len(target_waste_terms)}** termini senza vendite per la campagna **{selected_campaign_ai}**.")
                
                # B. Seleziona Contesto da Libreria
                st.markdown("##### 📌 Contesto Prodotto")
                use_library = st.checkbox("Usa prodotto dalla Libreria ASIN", value=True)
                
                product_context = ""
                
                if use_library and st.session_state['product_library']:
                    lib_options = [f"{p['brand']} - {p['name']} ({p['asin']})" for p in st.session_state['product_library']]
                    selected_prod_str = st.selectbox("Scegli Prodotto", lib_options)
                    
                    if selected_prod_str:
                        sel_asin = selected_prod_str.split("(")[-1].replace(")", "")
                        prod_data = next((p for p in st.session_state['product_library'] if p['asin'] == sel_asin), None)
                        if prod_data:
                            product_context = prod_data['context']
                            with st.expander("Vedi contesto caricato"):
                                st.text(product_context)
                else:
                    product_context = st.text_area("📄 Incolla qui il testo della Pagina Prodotto (Titolo, Bullet Points):", height=150, key="ai_context_manual")
                
                # C. Generazione
                if st.button("✨ Genera Analisi con Gemini"):
                    if not product_context:
                        st.error("Manca il contesto del prodotto (selezionalo dalla libreria o incollalo).")
                    elif target_waste_terms.empty:
                        st.error("Non ci sono termini da analizzare per questa campagna.")
                    else:
                        with st.spinner("Gemini sta analizzando i termini..."):
                            try:
                                genai.configure(api_key=api_key)
                                model = genai.GenerativeModel('gemini-pro')
                                
                                terms_list = target_waste_terms['Search Term'].head(150).tolist()
                                terms_str = "\n".join(terms_list)
                                
                                prompt = f"""
                                Analizza i termini di ricerca elencati qui sotto (provenienti dalla campagna "{selected_campaign_ai}") e il contenuto della pagina prodotto fornito.
                                
                                ELENCO TERMINI DI RICERCA (Senza vendite):
                                {terms_str}
                                
                                CONTENUTO PAGINA PRODOTTO:
                                {product_context}
                                
                                Dividi i termini di ricerca per asin e parole qualora ci siano degli asin nell’elenco.
                                Scrivi i termini di ricerca che devo inserire in corrispondenza negativa esatta.
                                
                                Fai 3 gruppi:
                                1. Assolutamente incoerente con la pagina prodotto.
                                2. Incoerente con il prodotto, ma con qualche affinità.
                                3. Parole chiave che sono affini ma semplicemente non hanno generato ordini.
                                
                                Scrivi i termini di ricerca senza parentesi o virgolette, incolonnati un termine di ricerca completo ogni riga.
                                """
                                response = model.generate_content(prompt)
                                st.success("Analisi completata!")
                                st.markdown(response.text)
                            except Exception as e:
                                st.error(f"Errore durante l'analisi AI: {e}")
            else:
                st.info("Nessun termine senza vendite trovato con i filtri attuali.")

        st.markdown("---")
        st.subheader("Suggerimenti AI (Regole Base)")
        suggestions = []
        for _, row in campaign_group.iterrows():
            if row['Sales'] == 0 and row['Spend'] >= threshold_spesa:
                suggestions.append(f"🔴 Blocca **{row['Campaign']}**: spesa €{row['Spend']:.2f} zero vendite")
            elif row['Sales'] > 0 and row['ACOS'] > acos_target:
                suggestions.append(f"🟡 Ottimizza **{row['Campaign']}**: ACOS {row['ACOS']:.2f}%")
        if suggestions:
            for s in suggestions[:5]: st.markdown(f"- {s}")
        else:
            st.success("Nessuna criticità rilevante.")

        st.subheader("🔥 Top 3 Criticità")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Portafogli peggiori**")
            pf_sorted = portfolio_group.copy().sort_values(by=['Sales', 'Spend'], ascending=[True, False]).head(3)
            for _, row in pf_sorted.iterrows():
                acos_display = f"{row['ACOS']:.2f}%" if pd.notna(row['ACOS']) else "N/A"
                st.error(f"{row['Portfolio']} (Spesa: €{row['Spend']:.2f}, ACOS: {acos_display})")
        with c2:
            st.markdown("**Campagne peggiori**")
            camp_sorted = campaign_group.copy().sort_values(by=['Sales', 'Spend'], ascending=[True, False]).head(3)
            for _, row in camp_sorted.iterrows():
                acos_display = f"{row['ACOS']:.2f}%" if pd.notna(row['ACOS']) else "N/A"
                st.error(f"{row['Campaign']} (Spesa: €{row['Spend']:.2f}, ACOS: {acos_display})")

# --- BRAND ANALYTICS ---
def show_brand_analytics():
    st.title("📈 Brand Analytics Insights")
    with st.expander("ℹ️ Guida", expanded=False):
        st.markdown("**File richiesto:** Prestazioni delle query di ricerca (CSV).")

    f = st.file_uploader("Carica File", type=["csv", "xlsx"])
    if f:
        df = load_data_robust(f)
        if df is None: return
        df = clean_columns(df)
        
        norm = lambda x: str(x).lower().strip().replace(" ", "_")
        cols = {norm(c): c for c in df.columns}
        def pk(*a): 
            for x in a: 
                if norm(x) in cols: return cols[norm(x)]
            return None

        q = pk("Query di ricerca", "search_query", "Termine di ricerca")
        vol = pk("Volume query di ricerca", "search_query_volume")
        i_tot = pk("Impressioni: conteggio totale", "search_funnel_impressions_total")
        i_br = pk("Impressioni: numero ASIN", "impressioni_numero_asin")
        c_tot = pk("Clic: conteggio totale", "search_funnel_clicks_total")
        c_br = pk("Clic: numero di ASIN", "clic_numero_asin")
        a_tot = pk("Aggiunte al carrello: conteggio totale", "search_funnel_add_to_carts_total")
        a_br = pk("Aggiunte al carrello: numero ASIN", "search_funnel_add_to_carts_brand_asin_count")
        b_tot = pk("Acquisti: conteggio totale", "search_funnel_purchases_total")
        b_br = pk("Acquisti: numero ASIN", "search_funnel_purchases_brand_asin_count")

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
        
        st.subheader("Risultati")
        st.dataframe(out.head(50), use_container_width=True)
        download_excel({"Brand Analytics": out}, "brand_analytics.xlsx")

# --- SQP ---
def show_sqp():
    st.title("🔎 SQP – Search Query Performance")
    with st.expander("ℹ️ Guida", expanded=False):
        st.markdown("**File richiesto:** Prestazioni query di ricerca (CSV).")

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
        download_excel({"SQP": df}, "sqp_analysis.xlsx")

# --- INVENTARIO FBA ---
def show_inventory():
    st.title("📦 Controllo Inventario FBA")
    with st.expander("ℹ️ Guida", expanded=False):
        st.markdown("**File richiesto:** Mastro dell'inventario (Inventory Ledger).")

    f = st.file_uploader("Carica File", type=["csv", "xlsx"])
    if f:
        df = load_data_robust(f)
        if df is None: return
        df = clean_columns(df)
        df.columns = df.columns.str.lower()

        req = ['starting warehouse balance', 'receipts', 'customer shipments', 'customer returns', 'found', 'lost', 'damaged', 'disposed', 'ending warehouse balance']
        for c in req:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        if 'ending warehouse balance' in df.columns:
            cols_inc = [c for c in ['receipts', 'customer returns', 'found'] if c in df.columns]
            cols_dec = [c for c in ['customer shipments', 'lost', 'damaged', 'disposed'] if c in df.columns]
            
            df['inc'] = df[cols_inc].sum(axis=1)
            df['dec'] = df[cols_dec].sum(axis=1).abs()
            
            df['ending_teorico'] = df.get('starting warehouse balance', 0) + df['inc'] - df['dec']
            df['delta'] = df['ending warehouse balance'] - df['ending_teorico']
            
            anomalies = df[df['delta'].abs() > 0.1].copy()
            
            st.subheader(f"📌 Anomalie 'Delta' (Teorico vs Reale): {len(anomalies)}")
            if not anomalies.empty:
                st.dataframe(anomalies)
                download_excel({"Anomalie": anomalies}, "reclami_fba.xlsx")
            else:
                st.success("Nessuna anomalia significativa rilevata.")

        if 'damaged' in df.columns and 'transaction type' in df.columns:
            damaged_transfer = df[
                (df['transaction type'].astype(str).str.lower().str.contains('adjustment')) & 
                (df['disposition'].isin(['damaged'])) &
                (df['damaged'] > 0)
            ].copy()
            
            if not damaged_transfer.empty:
                st.subheader(f"📦 Unità Danneggiate (Adjustment): {len(damaged_transfer)}")
                st.write("Queste unità sono state marcate come 'Damaged'. Verifica se sono state rimborsate.")
                st.dataframe(damaged_transfer)

# --- FUNNEL AUDIT ---
def show_funnel_audit():
    st.title("🧭 PPC Funnel Audit")
    with st.expander("ℹ️ Guida", expanded=False):
        st.markdown("**File richiesto:** File Macro (Campagne, Spesa, Vendite).")
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

        c_name = pick(df, ["Campagne", "Campaign", "Nome campagna"])
        c_spend = pick(df, ["Spesa", "Spend", "Costo"])
        c_sales = pick(df, ["Vendite", "Sales"])

        if not c_name:
            st.error("Colonne non trovate.")
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
        
        col1, col2 = st.columns([2, 1])
        with col1:
            try:
                import plotly.express as px
                fig = px.funnel(kpi, x='Spend', y='Layer', title="Spesa per Livello")
                st.plotly_chart(fig, use_container_width=True)
            except: st.bar_chart(kpi.set_index('Layer')['Spend'])
        with col2:
            st.dataframe(kpi.style.format({'Spend': '€{:.2f}', 'Sales': '€{:.2f}', 'ROAS': '{:.2f}'}))

# --- CORRISPETTIVI ---
def show_invoices():
    st.title("📄 Corrispettivi")
    with st.expander("ℹ️ Guida", expanded=False):
        st.markdown("**File richiesto:** Report Transazioni.")
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
                for c in cols_amt:
                    df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                
                df_grp = df.groupby(df[date_col].dt.date)[cols_amt].sum().reset_index()
                st.dataframe(df_grp, use_container_width=True)
                download_excel({"Corrispettivi": df_grp}, "corrispettivi.xlsx")
            else: st.error("Colonne importi non trovate.")
        else: st.error("Colonna data non trovata.")

# ==============================================================================
# 5. MAIN NAVIGATOR
# ==============================================================================
def main():
    with st.sidebar:
        # LOGO
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
            st.markdown("""
            <div style='background-color: #2940A8; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;'>
                <h1 style='color: white !important; margin: 0; font-size: 40px;'>S<span style='color: #FA7838;'>Z</span></h1>
                <p style='color: white; margin: 5px 0 0 0; font-size: 10px; letter-spacing: 2px; font-weight: 600;'>SALESZONE</p>
            </div>
            """, unsafe_allow_html=True)
        
        # API Key (Da Secrets o Input)
        st.markdown("### 🔑 Impostazioni AI")
        
        if "GEMINI_API_KEY" in st.secrets:
            # Se la chiave è nei secrets, la carichiamo ma mostriamo un indicatore
            st.session_state['gemini_api_key'] = st.secrets["GEMINI_API_KEY"]
            st.success("✅ API Key caricata da Secrets")
        else:
            # Altrimenti input manuale
            api_key = st.text_input("Gemini API Key", type="password", help="Inserisci la chiave per l'AI Consultant")
            if api_key: st.session_state['gemini_api_key'] = api_key
        
        st.markdown("---")
        
        MENU_VOCI = [
            "Home", "Libreria Prodotti", "PPC Optimizer", "Brand Analytics Insights", "SQP – Search Query Performance",
            "Generazione Corrispettivi", "Controllo Inventario FBA", "Funnel Audit"
        ]
        selected = st.radio("Naviga", MENU_VOCI, label_visibility="collapsed")
        st.markdown("---")
        st.caption("© 2025 Saleszone Agency")

    if selected == "Home": show_home()
    elif selected == "Libreria Prodotti": show_product_library()
    elif selected == "PPC Optimizer": show_ppc_optimizer()
    elif selected == "Brand Analytics Insights": show_brand_analytics()
    elif selected == "SQP – Search Query Performance": show_sqp()
    elif selected == "Generazione Corrispettivi": show_invoices()
    elif selected == "Controllo Inventario FBA": show_inventory()
    elif selected == "Funnel Audit": show_funnel_audit()

if __name__ == "__main__":
    main()
