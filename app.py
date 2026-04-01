import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai

st.set_page_config(page_title="Istobal AI Auditor", layout="wide")
st.title("📊 Monitor de Visibilidad IA: ISTOBAL")

# 1. Cargar llaves
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("Faltan las API Keys en los Secrets de Streamlit.")
    st.stop()

# 2. Inicializar clientes
client_openai = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model_gemini = genai.GenerativeModel('models/gemini-1.5-flash')

# 3. Interfaz
brand = st.sidebar.text_input("Marca:", "Istobal")
prompts_text = st.sidebar.text_area("Prompts (uno por línea):", "¿Es Istobal líder en lavado?")
prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]

if st.button("Ejecutar"):
    results = []
    for p in prompts:
        # GPT
        try:
            res_gpt = client_openai.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": p}]
            ).choices[0].message.content
        except Exception as e:
            res_gpt = f"Error GPT: {e}"

        # Gemini
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Probamos con el nombre técnico más estándar
    model_gemini = genai.GenerativeModel('gemini-1.5-flash-latest') 
except Exception as e:
    st.error(f"Error al configurar Gemini: {e}")

        results.append({
            "Pregunta": p,
            "ChatGPT": res_gpt,
            "Gemini": res_gem,
            "En GPT": brand.lower() in res_gpt.lower(),
            "En Gemini": brand.lower() in res_gem.lower()
        })
    
    st.dataframe(pd.DataFrame(results))
