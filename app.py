import streamlit as st
import pandas as pd
import openai
import requests

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Istobal AI Auditor", page_icon="🧼", layout="wide")

st.title("📊 Monitor de Visibilidad IA: ISTOBAL")
st.markdown("Analiza la presencia de la marca en ChatGPT y Gemini (v1 estable).")

# --- 2. CARGA DE CLAVES DESDE SECRETS ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ Faltan las API Keys en los 'Secrets' de Streamlit. Revisa la configuración del panel.")
    st.stop()

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# --- 3. CONFIGURACIÓN DE CLIENTES ---
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)

# --- 4. INTERFAZ LATERAL ---
st.sidebar.header("Parámetros de Auditoría")
brand_to_track = st.sidebar.text_input("Marca a monitorizar:", "Istobal")
prompts_raw = st.sidebar.text_area(
    "Prompts (uno por línea):",
    "¿Quién lidera el sector de lavado industrial?\nCompara Istobal y WashTec en digitalización\nVentajas de Smartwash Istobal"
)

prompts = [p.strip() for p in prompts_raw.split('\n') if p.strip()]

# --- 5. LÓGICA DE EJECUCIÓN ---
if st.button("🚀 Iniciar Análisis"):
    if not prompts:
        st.warning("Por favor, introduce al menos un prompt para analizar.")
    else:
        results = []
        progress_bar = st.progress(0)
        
        for i, p in enumerate(prompts):
            # --- A. CONSULTA CHATGPT (GPT-4o) ---
            try:
                res_gpt = client_openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": p}]
                ).choices[0].message.content
            except Exception as e:
                res_gpt = f"Error GPT: {str(e)}"

            # --- B. CONSULTA GEMINI (Vía API REST V1 Estable) ---
            try:
                # Usamos la versión v1 que es la más compatible en 2026
                gemini_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": p}]}]
                }
                
                response = requests.post(gemini_url, json=payload, timeout=15)
                response_json = response.json()
                
                if response.status_code == 200:
                    # Navegamos por el JSON de respuesta de Google
                    res_gem = response_json['candidates'][0]['content']['parts'][0]['text']
                else:
                    # Si falla, capturamos el mensaje de error real de Google
                    error_info = response_json.get('error', {}).get('message', 'Error desconocido')
                    res_gem = f"Error {response.status_code}: {error_info}"
                    
            except Exception as e:
                res_gem = f"Error de conexión Gemini: {str(e)}"

            # --- C. PROCESAMIENTO ---
            results.append({
                "Prompt": p,
                "Respuesta ChatGPT": res_gpt,
                "Respuesta Gemini": res_gem,
                "Encontrado en GPT": brand_to_track.lower() in res_gpt.lower(),
                "Encontrado en Gemini": brand_to_track.lower() in res_gem.lower()
            })
            progress_bar.progress((i + 1) / len(prompts))

        # --- 6. VISUALIZACIÓN DE RESULTADOS ---
        df = pd.DataFrame(results)

        # Métricas principales
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Visibilidad ChatGPT", f"{(df['Encontrado en GPT'].mean()*100):.0f}%")
        with c2:
            st.metric("Visibilidad Gemini", f"{(df['Encontrado en Gemini'].mean()*100):.0f}%")

        # Tabla detallada
        st.subheader("Resultados del Análisis")
        st.dataframe(df, use_container_width=True)

        # Botón de exportación
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte en CSV",
            data=csv,
            file_name="auditoria_istobal_ai.csv",
            mime="text/csv"
        )

st.divider()
st.caption("Herramienta desarrollada para el equipo de Istobal. Las respuestas dependen de los datos de entrenamiento de los modelos.")
