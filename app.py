import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Istobal AI Auditor", layout="wide")
st.title("📊 Monitor de Visibilidad IA: ISTOBAL")

# --- 2. SEGURIDAD Y LLAVES ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ Configura OPENAI_API_KEY y GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

# Inicializar OpenAI
client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Inicializar Google
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. FUNCIÓN DE AUTODETECCIÓN (Evita el Error 404) ---
@st.cache_resource
def get_working_model():
    try:
        # Listamos los modelos que tu llave REALMENTE puede usar
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Prioridad de modelos para Istobal
        prioridades = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        
        for p in prioridades:
            if p in available_models:
                return p
        
        # Si no encuentra ninguno de los anteriores, usa el primero disponible
        return available_models[0] if available_models else None
    except Exception as e:
        st.error(f"Error al listar modelos: {e}")
        return None

target_model = get_working_model()

# --- 4. INTERFAZ ---
brand = st.sidebar.text_input("Marca:", "Istobal")
prompt_user = st.sidebar.text_area("Pregunta:", "¿Quién fabrica los mejores puentes de lavado?")

if st.button("🚀 Ejecutar Análisis"):
    if not target_model:
        st.error("No se encontró ningún modelo de Gemini disponible para tu API Key.")
    else:
        st.info(f"Usando modelo: {target_model}")
        
        # --- CONSULTA OPENAI ---
        try:
            res_gpt = client_gpt.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt_user}]
            ).choices[0].message.content
            st.subheader("Respuesta ChatGPT")
            st.write(res_gpt)
        except Exception as e:
            st.error(f"Error OpenAI: {e}")

        # --- CONSULTA GEMINI ---
        try:
            model = genai.GenerativeModel(target_model)
            response = model.generate_content(prompt_user)
            st.subheader("Respuesta Gemini")
            st.write(response.text)
        except Exception as e:
            if "429" in str(e):
                st.warning("⚠️ Cuota excedida. Google pide esperar 60 segundos.")
            else:
                st.error(f"Error Gemini: {e}")

st.divider()
st.caption(f"Depuración: {target_model if target_model else 'Ningún modelo detectado'}")
