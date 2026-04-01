import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

st.set_page_config(page_title="Istobal AI Auditor", layout="wide", page_icon="🧼")

# --- 1. CONFIGURACIÓN DE APIS ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("Faltan las API Keys en los Secrets de Streamlit.")
    st.stop()

client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. FUNCIÓN PARA ENCONTRAR EL MODELO CORRECTO ---
@st.cache_resource
def get_valid_model_name():
    try:
        # Listamos modelos disponibles para tu cuenta
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Intentamos buscar el flash 1.5 en la lista
        for target in ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.5-pro"]:
            if target in models:
                return target
        return models[0] if models else "gemini-pro"
    except:
        # Si falla el listado, probamos el nombre corto (a veces funciona mejor)
        return "gemini-1.5-flash"

# --- 3. INTERFAZ ---
st.title("📊 Auditoría de Visibilidad: ISTOBAL")
target_model = get_valid_model_name()

with st.sidebar:
    brand = st.text_input("Marca a buscar:", "Istobal")
    prompt_input = st.text_area("Pregunta / Prompt:")
    st.info(f"Modelo activo: {target_model}")

# --- 4. LÓGICA DE EJECUCIÓN ---
if st.button("🚀 Ejecutar Análisis"):
    if not prompt_input:
        st.warning("Escribe un prompt.")
    else:
        # Inicializamos para evitar el NameError
        res_gpt = "Sin respuesta"
        res_gem = "Sin respuesta"
        
        col1, col2 = st.columns(2)
        
        # --- BLOQUE CHATGPT ---
        with col1:
            st.subheader("ChatGPT")
            try:
                chat_res = client_gpt.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt_input}]
                )
                res_gpt = chat_res.choices[0].message.content
                st.write(res_gpt)
            except Exception as e:
                res_gpt = f"Error OpenAI: {e}"
                st.error(res_gpt)

        # --- BLOQUE GEMINI ---
        with col2:
            st.subheader("Gemini")
            try:
                # Usamos el nombre que la función detectó como válido
                model_gemini = genai.GenerativeModel(target_model)
                response = model_gemini.generate_content(prompt_input)
                res_gem = response.text
                st.write(res_gem)
            except Exception as e:
                res_gem = f"Error Gemini: {e}"
                st.error(res_gem)

        # --- 5. TABLA RESUMEN ---
        st.divider()
        menciona_gpt = "✅ SÍ" if brand.lower() in res_gpt.lower() else "❌ NO"
        menciona_gem = "✅ SÍ" if brand.lower() in res_gem.lower() else "❌ NO"
        
        if "Error" in res_gpt: menciona_gpt = "⚠️ ERROR"
        if "Error" in res_gem: menciona_gem = "⚠️ ERROR"

        df_resumen = pd.DataFrame({
            "IA": ["ChatGPT", "Gemini"],
            "¿Menciona a Istobal?": [menciona_gpt, menciona_gem]
        })
        st.table(df_resumen)
