import streamlit as st
import google.generativeai as genai

st.title("🛠️ Gemini API Tester")

# 1. Inserisci la tua chiave qui (o leggila dai secrets se già impostati)
api_key = st.text_input("Inserisci la tua API Key di Gemini:", type="password")

if api_key:
    # Configura
    genai.configure(api_key=api_key)
    
    st.write("---")
    st.subheader("🔍 Modelli Disponibili per la tua Chiave:")
    
    try:
        # Chiede a Google la lista dei modelli
        models = genai.list_models()
        
        found_any = False
        for m in models:
            # Filtra solo quelli che possono generare testo (generateContent)
            if 'generateContent' in m.supported_generation_methods:
                st.success(f"✅ Modello trovato: **{m.name}**")
                st.code(f"model = genai.GenerativeModel('{m.name}')")
                found_any = True
        
        if not found_any:
            st.warning("Nessun modello di generazione testo trovato per questa chiave.")
            
    except Exception as e:
        st.error(f"Errore di connessione: {e}")

    st.write("---")
    st.subheader("🧪 Test di Generazione")
    model_name = st.text_input("Copia qui il nome di un modello trovato sopra (es. models/gemini-pro):")
    
    if st.button("Prova a generare testo"):
        if model_name:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Ciao, se mi leggi rispondi con 'Funziona!'")
                st.success("Risposta ricevuta:")
                st.write(response.text)
            except Exception as e:
                st.error(f"Errore durante la generazione: {e}")
