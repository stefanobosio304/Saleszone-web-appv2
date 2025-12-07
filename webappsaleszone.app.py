import streamlit as st
import pandas as pd
import numpy as np
import io
import re
from io import BytesIO

# ==============================================================================
# 1. CONFIGURAZIONE PAGINA (PRIMA ISTRUZIONE)
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
        h1, h2, h3 {
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
        /* Logo Sidebar */
        .sidebar-logo {
            font-size: 28px;
            font-weight: 800;
            color: #2940A8;
            margin-bottom: 20px;
        }
        .sidebar-logo span {
            color: #FA7838;
        }
        /* Alert */
        .stAlert {
            background-color: #eef2ff;
            border: 1px solid #2940A8;
            color: #2940A8;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==============================================================================
# 3. UTILITIES GLOBALI
# ==============================================================================
def load_data(file):
    """Carica CSV o Excel gestendo errori e separatori."""
    if file is None: return None
    try:
        if file.name.endswith('.csv'):
            try:
                df = pd.read_csv(file, encoding='utf-8')
                if df.shape[1] < 2:
                    file.seek(0)
                    df = pd.read_csv(file, sep=';', encoding='utf-8')
            except:
                file.seek(0)
                df = pd.read_csv(file, sep=';', encoding='latin1')
        else:
            df = pd.read_excel(file, engine='openpyxl')
        
        # Pulizia nomi colonne
        df.columns = df.columns.str.strip().str.replace("\ufeff", "")
        return df
    except Exception as e:
        st.error(f"Errore lettura file: {e}")
        return None

def download_excel(dfs_dict, filename):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        for sheet_name, df in dfs_dict.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    
    st.download_button(
        label=f"📥 Scarica {filename}",
        data=buffer.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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
    st.title("📊 PPC Ads Optimizer")
    col1, col2 = st.columns(2)
    with col1:
        file = st.file_uploader("Carica Report Search Term", type=["csv", "xlsx"])
    with col2:
        acos_target = st.number_input("ACOS Target (%)", 1, 100, 30)
        click_min = st.number_input("Click minimi senza vendite", 1, 100, 10)

    if file:
        df = load_data(file)
        if df is None: return

        # Mapping intelligente
        col_map = {
            'Targeting': 'Keyword', 'Termine ricerca cliente': 'Search Term', 'Customer Search Term': 'Search Term',
            'Impressioni': 'Impressions', 'Clic': 'Clicks', 'Spesa': 'Spend', 'Cost': 'Spend',
            'Vendite totali (€) 7 giorni': 'Sales', '7 Day Total Sales': 'Sales',
            'Totale ordini (#) 7 giorni': 'Orders', '7 Day Total Orders': 'Orders',
            'Nome campagna': 'Campaign', 'Nome portafoglio': 'Portfolio'
        }
        df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)
        
        req = ['Impressions', 'Clicks', 'Spend', 'Sales', 'Orders']
        # Gestione colonne mancanti o nomi diversi (inglese/italiano)
        missing = [c for c in req if c not in df.columns]
        if missing:
            # Tentativo fallback case-insensitive
            lower_cols = {c.lower(): c for c in df.columns}
            for m in missing:
                if m.lower() in lower_cols:
                    df.rename(columns={lower_cols[m.lower()]: m}, inplace=True)
            
            # Ricontrollo
            missing = [c for c in req if c not in df.columns]
            if missing:
                st.error(f"Colonne mancanti: {missing}")
                return

        # Conversione numerica
        for c in req:
            if df[c].dtype == object:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            else:
                df[c] = df[c].fillna(0)

        # Calcolo KPI
        df['ACOS'] = df.apply(lambda x: (x['Spend']/x['Sales']*100) if x['Sales'] > 0 else 0, axis=1)
        df['ROAS'] = df.apply(lambda x: (x['Sales']/x['Spend']) if x['Spend'] > 0 else 0, axis=1)
        df['CPC'] = (df['Spend'] / df['Clicks']).fillna(0)

        # KPI Globali
        tot_spend = df['Spend'].sum()
        tot_sales = df['Sales'].sum()
        tot_acos = (tot_spend/tot_sales*100) if tot_sales > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Spesa Totale", f"€ {tot_spend:,.2f}")
        k2.metric("Vendite Totali", f"€ {tot_sales:,.2f}")
        k3.metric("ACOS Globale", f"{tot_acos:.2f}%")
        k4.metric("ROAS Globale", f"{tot_sales/tot_spend:.2f}" if tot_spend > 0 else "0")

        # Analisi
        st.markdown("### 🔍 Analisi e Suggerimenti")
        
        # Bleeding
        bleeding = df[(df['Sales'] == 0) & (df['Clicks'] >= click_min)].sort_values('Spend', ascending=False)
        if not bleeding.empty:
            st.error(f"🔴 **Sprechi Rilevati:** {len(bleeding)} termini stanno spendendo senza convertire.")
            st.dataframe(bleeding[['Campaign', 'Search Term', 'Clicks', 'Spend', 'CPC']].style.format({'Spend': '€{:.2f}'}), use_container_width=True)
        else:
            st.success("Nessun termine con spreco elevato rilevato.")

        # Winners
        winners = df[(df['Sales'] > 0) & (df['ACOS'] < acos_target)].sort_values('Sales', ascending=False)
        if not winners.empty:
            st.success(f"🟢 **Opportunità:** {len(winners)} termini performano sotto il target ACOS.")
            st.dataframe(winners[['Campaign', 'Search Term', 'Sales', 'ACOS', 'ROAS']].style.format({'Sales': '€{:.2f}', 'ACOS': '{:.2f}%'}), use_container_width=True)

# --- BRAND ANALYTICS ---
def show_brand_analytics():
    st.title("📈 Brand Analytics")
    file = st.file_uploader("Carica CSV Brand Analytics", type=["csv"])
    if file:
        df = load_data(file)
        if df is None: return

        # Mappatura Colonne
        map_ba = {}
        for c in df.columns:
            cl = c.lower()
            if 'query' in cl and 'volume' in cl: map_ba['Volume'] = c
            elif 'query' in cl: map_ba['Query'] = c
            elif 'totale' in cl and 'clic' in cl: map_ba['Click Tot'] = c
            elif 'totale' in cl and 'impressioni' in cl: map_ba['Impressioni Tot'] = c
            elif 'marchio' in cl and 'clic' in cl: map_ba['Click Brand'] = c
            elif 'marchio' in cl and 'impressioni' in cl: map_ba['Impressioni Brand'] = c
            elif 'marchio' in cl and 'acquisti' in cl: map_ba['Acquisti Brand'] = c
            elif 'totale' in cl and 'acquisti' in cl: map_ba['Acquisti Tot'] = c

        if 'Query' not in map_ba:
            st.error("Formato file non riconosciuto.")
            return

        data = pd.DataFrame()
        data['Query'] = df[map_ba['Query']]
        # Pulizia numeri (rimozione virgole etc)
        for k in ['Volume', 'Impressioni Tot', 'Impressioni Brand', 'Click Tot', 'Click Brand']:
            if k in map_ba:
                col_name = map_ba[k]
                if df[col_name].dtype == object:
                    data[k] = pd.to_numeric(df[col_name].astype(str).str.replace(',', '').str.replace('.', ''), errors='coerce').fillna(0)
                else:
                    data[k] = df[col_name].fillna(0)
            else:
                data[k] = 0

        # Calcoli Share
        data['Impression Share'] = (data['Impressioni Brand'] / data['Impressioni Tot'] * 100).fillna(0)
        data['Click Share'] = (data['Click Brand'] / data['Click Tot'] * 100).fillna(0)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Volume Totale", f"{data['Volume'].sum():,.0f}")
        c2.metric("Click Share Medio", f"{data['Click Share'].mean():.2f}%")
        c3.metric("Impression Share Media", f"{data['Impression Share'].mean():.2f}%")

        st.dataframe(data[['Query', 'Volume', 'Impression Share', 'Click Share']].sort_values('Volume', ascending=False).style.format({
            'Volume': '{:,.0f}', 'Impression Share': '{:.2f}%', 'Click Share': '{:.2f}%'
        }), use_container_width=True)
        
        download_excel({"Brand Analytics": data}, "ba_analysis.xlsx")

# --- INVENTARIO FBA ---
def show_inventory():
    st.title("📦 Controllo Inventario FBA")
    st.info("Carica il report 'Inventory Ledger' (Mastro Inventario) per identificare unità perse.")
    file = st.file_uploader("Carica file", type=["csv", "xlsx"])
    
    if file:
        df = load_data(file)
        if df is None: return
        df.columns = [c.lower().strip() for c in df.columns]

        # Logica avanzata per individuare le colonne
        req = ['fnsku', 'transaction type', 'quantity', 'disposition']
        mapped = {}
        for r in req:
            found = [c for c in df.columns if r in c]
            if found: mapped[r] = found[0]
        
        if len(mapped) < 3:
            st.error(f"Colonne essenziali mancanti. Trovate: {list(df.columns)}")
            return

        df['qty'] = pd.to_numeric(df[mapped.get('quantity')], errors='coerce').fillna(0)
        df['type'] = df[mapped.get('transaction type')].astype(str).str.lower()
        df['disposition'] = df[mapped.get('disposition')].astype(str).str.lower()

        # Analisi Lost vs Found
        lost = df[df['type'].str.contains('adjustment') & df['disposition'].isin(['lost', 'damaged'])]
        found = df[df['type'].str.contains('adjustment') & df['disposition'].isin(['found'])]
        
        lost_grp = lost.groupby('fnsku')['qty'].sum().abs()
        found_grp = found.groupby('fnsku')['qty'].sum()
        
        res = pd.DataFrame({'Persi/Danneggiati': lost_grp, 'Ritrovati': found_grp}).fillna(0)
        res['Differenza (Da Rimborsare)'] = res['Persi/Danneggiati'] - res['Ritrovati']
        
        claims = res[res['Differenza (Da Rimborsare)'] > 0].sort_values('Differenza (Da Rimborsare)', ascending=False)

        st.markdown("### 🕵️ Risultati Analisi")
        if not claims.empty:
            st.warning(f"Rilevate **{len(claims)}** discrepanze rimborsabili.")
            st.dataframe(claims)
            download_excel({"Reclami FBA": claims}, "reclami_fba.xlsx")
        else:
            st.success("Tutte le unità perse/danneggiate risultano rimborsate o ritrovate.")

# --- FUNNEL AUDIT ---
def show_funnel_audit():
    st.title("🧭 Funnel Audit")
    st.markdown("Analisi della distribuzione del budget per fase del funnel (TOFU/MOFU/BOFU).")
    
    file = st.file_uploader("Carica File Macro (Excel/CSV)", type=['xlsx', 'csv'])
    if file:
        df = load_data(file)
        if df is None: return

        # Cerca colonne chiave
        try:
            camp_col = [c for c in df.columns if 'campagn' in c.lower() or 'campaign' in c.lower()][0]
            spend_col = [c for c in df.columns if 'spesa' in c.lower() or 'spend' in c.lower()][0]
            sales_col = [c for c in df.columns if 'vendite' in c.lower() or 'sales' in c.lower()][0]
        except:
            st.error("Impossibile trovare le colonne Campagna/Spesa/Vendite.")
            return

        # Pulizia dati
        df['Spesa'] = pd.to_numeric(df[spend_col], errors='coerce').fillna(0)
        df['Vendite'] = pd.to_numeric(df[sales_col], errors='coerce').fillna(0)

        # Logica classificazione (Semplificata dal codice originale)
        def get_stage(name):
            n = str(name).upper()
            if any(x in n for x in ['BRAND', 'PROTECTION', 'DEFENSE', 'REMARKETING']): return 'BOFU (Difesa)'
            if any(x in n for x in ['COMPETITOR', 'EXACT', 'PAT']): return 'MOFU (Competitività)'
            if any(x in n for x in ['GENERIC', 'BROAD', 'AUTO', 'CATEGORY']): return 'TOFU (Scoperta)'
            return 'Non Classificato'

        df['Stage'] = df[camp_col].apply(get_stage)
        
        # Aggregazione
        funnel = df.groupby('Stage')[['Spesa', 'Vendite']].sum().reset_index()
        funnel['ROAS'] = funnel['Vendite'] / funnel['Spesa']
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(data=funnel.set_index('Stage')['Spesa'], color='#2940A8')
        with col2:
            st.dataframe(funnel.style.format({'Spesa': '€{:,.2f}', 'Vendite': '€{:,.2f}', 'ROAS': '{:.2f}'}), use_container_width=True)

# --- CORRISPETTIVI ---
def show_invoices():
    st.title("📄 Generazione Corrispettivi")
    file = st.file_uploader("Carica Report Transazioni (CSV)", type=['csv'])
    if file:
        df = load_data(file)
        if df is None: return
        
        # Cerca colonne date/amount
        dt_cols = [c for c in df.columns if 'date' in c.lower() or 'data' in c.lower()]
        amt_cols = [c for c in df.columns if 'total' in c.lower() or 'amount' in c.lower()]
        
        if dt_cols and amt_cols:
            d_col, a_col = dt_cols[0], amt_cols[0]
            df[d_col] = pd.to_datetime(df[d_col], errors='coerce')
            df[a_col] = pd.to_numeric(df[a_col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            daily = df.groupby(df[d_col].dt.date)[a_col].sum().reset_index()
            daily.columns = ['Data', 'Totale (€)']
            
            st.dataframe(daily.style.format({'Totale (€)': '€{:,.2f}'}), use_container_width=True)
            download_excel({"Corrispettivi": daily}, "corrispettivi_mese.xlsx")
        else:
            st.error("Colonne Data/Importo non trovate.")

# --- PLACEHOLDER SQP ---
def show_sqp():
    st.title("🔎 Search Query Performance")
    st.info("In arrivo: Analisi avanzata del funnel di ricerca.")

# ==============================================================================
# 5. MAIN
# ==============================================================================
def main():
    with st.sidebar:
        st.markdown("<div class='sidebar-logo'>S<span>Z</span> SALESZONE</div>", unsafe_allow_html=True)
        selected = st.radio(
            "Menu Principale",
            ["Home", "PPC Optimizer", "Brand Analytics", "Inventario FBA", "Funnel Audit", "Corrispettivi", "SQP Analysis"],
            label_visibility="collapsed"
        )
        st.markdown("---")
        st.caption("© 2025 Saleszone Agency")

    if selected == "Home": show_home()
    elif selected == "PPC Optimizer": show_ppc_optimizer()
    elif selected == "Brand Analytics": show_brand_analytics()
    elif selected == "Inventario FBA": show_inventory()
    elif selected == "Funnel Audit": show_funnel_audit()
    elif selected == "Corrispettivi": show_invoices()
    elif selected == "SQP Analysis": show_sqp()

if __name__ == "__main__":
    main()