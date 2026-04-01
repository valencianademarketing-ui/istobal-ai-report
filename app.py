import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

st.set_page_config(page_title="Istobal AI Auditor", layout="wide")

# Configuración robusta
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
GEMINI_KEY = st.secrets["GEMINI_API_KEY"]

client_gpt = openai.OpenAI(api_key=OPENAI_KEY)
genai.configure(api_key=GEMINI_KEY)

# USAR 1.5 FLASH (Más estable para Free Tier)
model_google = genai.GenerativeModel('gemini-1.5-flash')

p = st.text_input("Prompt de prueba:", "¿Qué fabrica Istobal?")

if st.button("Analizar"):
    # GPT-4o
    try:
        res_gpt = client_gpt.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": p}]
        ).choices[0].message.content
        st.write(f"**GPT:** {res_gpt}")
    except Exception as e:
        st.error(f"Error GPT: {e}")

    # GEMINI con reintento automático
    with st.spinner("Esperando respuesta de Google..."):
        for intento in range(3):
            try:
                response = model_google.generate_content(p)
                st.write(f"**Gemini:** {response.text}")
                break
            except Exception as e:
                if "429" in str(e):
                    st.warning(f"Intento {intento+1}: Reintentando en 5 segundos...")
                    time.sleep(5)
                else:
                    st.error(f"Error: {e}")
                    break
