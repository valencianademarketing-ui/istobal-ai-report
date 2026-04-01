import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

st.set_page_config(page_title="Istobal AI Auditor", layout="wide")

# Configuración de clientes
client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# FORZAMOS EL MODELO 1.5 FLASH (El que mejor funciona tras poner la tarjeta)
model_gemini = genai.GenerativeModel('gemini-1.5-flash')

brand = st.sidebar.text_input("Marca:", "Istobal")
prompt = st.sidebar.text_input("Pregunta:")

if st.button("🚀 Ejecutar Auditoría"):
    if not prompt:
        st.error("Escribe algo.")
    else:
        # Fila de resultados
        col1, col2 = st.columns(2)
        
        # --- BLOQUE CHATGPT ---
        with col1:
            try:
                res_gpt = client_gpt.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                ).choices[0].message.content
                st.info("Respuesta ChatGPT")
                st.write(res_gpt)
                st.write(f"**Menciona a {brand}:** {'✅ SÍ' if brand.lower() in res_gpt.lower() else '❌ NO'}")
            except Exception as e:
                st.error(f"Error OpenAI: {e}")

        # --- BLOQUE GEMINI ---
        with col2:
            try:
                # Pequeño delay de cortesía
                time.sleep(1)
                response = model_gemini.generate_content(prompt)
                res_gem = response.text
                st.success("Respuesta Gemini")
                st.write(res_gem)
                st.write(f"**Menciona a {brand}:** {'✅ SÍ' if brand.lower() in res_gem.lower() else '❌ NO'}")
            except Exception as e:
                if "429" in str(e):
                    st.error("🚨 Sigue saliendo Error 429. Google tarda unos minutos en procesar tu tarjeta. Refresca en 5 min.")
                else:
                    st.error(f"Error Gemini: {e}")

        # --- TABLA RESUMEN ---
        st.divider()
        df = pd.DataFrame({
            "IA": ["ChatGPT", "Gemini"],
            "Presencia": ["✅" if brand.lower() in res_gpt.lower() else "❌", 
                          "✅" if brand.lower() in res_gem.lower() else "❌"]
        })
        st.table(df)
