import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Istobal AI Auditor", layout="wide")
st.title("📊 Monitor de Visibilidad IA: ISTOBAL")

# --- CARGA DE CLAVES ---
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    # Configuración de OpenAI
    client_gpt = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    # Configuración de Google (SDK Oficial)
    genai.configure(api_key=GEMINI_API_KEY)
    
except Exception as e:
    st.error("⚠️ Revisa tus Secrets en Streamlit. Asegúrate de que los nombres sean exactos.")
    st.stop()

# --- INTERFAZ ---
brand = st.sidebar.text_input("Marca a buscar:", "Istobal")
prompts_text = st.sidebar.text_area("Prompts (uno por línea):", "¿Quién lidera el sector de lavado?")
prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]

if st.button("🚀 Ejecutar Auditoría"):
    results = []
    
    # Definimos el modelo aquí dentro para asegurar que use la última config
    # Usamos gemini-1.5-flash que es el estándar actual
    model_gemini = genai.GenerativeModel('gemini-1.5-flash')

    for p in prompts:
        # --- BLOQUE CHATGPT ---
        try:
            res_gpt = client_gpt.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": p}]
            ).choices[0].message.content
        except Exception as e:
            res_gpt = f"Error GPT: {e}"

        # --- BLOQUE GEMINI (SDK Oficial con manejo de error 404) ---
        try:
            response = model_gemini.generate_content(p)
            res_gem = response.text
        except Exception as e:
            # Si el SDK falla, intentamos una variante de nombre que a veces desbloquea el 404
            try:
                model_alt = genai.GenerativeModel('models/gemini-1.5-flash')
                res_gem = model_alt.generate_content(p).text
            except:
                res_gem = f"Error Gemini: El modelo no está disponible en tu región/cuenta. Detalle: {e}"

        results.append({
            "Prompt": p,
            "ChatGPT": res_gpt,
            "Gemini": res_gem,
            "Visto": brand.lower() in res_gpt.lower() or brand.lower() in res_gem.lower()
        })

    st.dataframe(pd.DataFrame(results), use_container_width=True)

st.info("Nota: Si Gemini sigue dando error 404, es probable que la IP del servidor de Streamlit esté en una región no soportada por el plan gratuito de Google.")
