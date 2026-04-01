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
model_gemini = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. INTERFAZ ---
st.title("📊 Auditoría de Visibilidad: ISTOBAL")

with st.sidebar:
    brand = st.text_input("Marca a buscar:", "Istobal")
    prompt_input = st.text_area("Pregunta / Prompt:")
    st.info("Nota: Si acabas de poner la tarjeta en Google, espera 10-15 min a que el error 429 desaparezca.")

# --- 3. LÓGICA DE EJECUCIÓN ---
if st.button("🚀 Ejecutar Análisis"):
    if not prompt_input:
        st.warning("Por favor, escribe un prompt.")
    else:
        # Inicializamos las variables para evitar el NameError
        res_gpt = "Error o sin respuesta"
        res_gem = "Error o sin respuesta"
        
        col1, col2 = st.columns(2)
        
        # --- BLOQUE CHATGPT ---
        with col1:
            st.subheader("ChatGPT (OpenAI)")
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
            st.subheader("Gemini (Google)")
            try:
                # Pausa de seguridad por si la IP está saturada
                time.sleep(2) 
                response = model_gemini.generate_content(prompt_input)
                res_gem = response.text
                st.write(res_gem)
            except Exception as e:
                res_gem = f"Error Gemini: {e}"
                st.error(res_gem)

        # --- 4. TABLA COMPARATIVA (Blindada contra NameError) ---
        st.divider()
        st.subheader("Resumen de Visibilidad")
        
        # Calculamos la presencia de marca de forma segura
        menciona_gpt = "✅ SÍ" if brand.lower() in res_gpt.lower() else "❌ NO"
        menciona_gem = "✅ SÍ" if brand.lower() in res_gem.lower() else "❌ NO"
        
        # Si hubo un error real en la respuesta, lo marcamos
        if "Error Gemini" in res_gem: menciona_gem = "⚠️ FALLO TÉCNICO"
        if "Error OpenAI" in res_gpt: menciona_gpt = "⚠️ FALLO TÉCNICO"

        df_resumen = pd.DataFrame({
            "Modelo IA": ["ChatGPT (GPT-4o)", "Gemini (1.5-Flash)"],
            "¿Menciona a la marca?": [menciona_gpt, menciona_gem]
        })
        
        st.table(df_resumen)
