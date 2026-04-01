import streamlit as st
import pandas as pd
import openai
import requests

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Istobal AI Auditor", page_icon="🧼", layout="wide")

st.title("📊 Monitor de Visibilidad IA: ISTOBAL")
st.markdown("Analiza en tiempo real la presencia de la marca en ChatGPT y Gemini.")

# --- CARGA DE CLAVES DESDE SECRETS ---
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("⚠️ Error: No se han encontrado las claves 'OPENAI_API_KEY' o 'GEMINI_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- CONFIGURACIÓN CLIENTES ---
client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)

# --- BARRA LATERAL ---
st.sidebar.header("Configuración")
brand_to_track = st.sidebar.text_input("Marca a monitorizar:", "Istobal")
prompts_raw = st.sidebar.text_area(
    "Prompts (uno por línea):",
    "¿Quién lidera el sector de lavado industrial?\nCompara Istobal y WashTec en digitalización\nMejores puentes de lavado automáticos 2026"
)

prompts = [p.strip() for p in prompts_raw.split('\n') if p.strip()]

# --- LÓGICA DE EJECUCIÓN ---
if st.button("🚀 Ejecutar Auditoría"):
    if not prompts:
        st.warning("Introduce al menos un prompt.")
    else:
        results = []
        progress_bar = st.progress(0)
        
        for i, p in enumerate(prompts):
            # 1. CONSULTA CHATGPT
            try:
                res_gpt = client_openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": p}]
                ).choices[0].message.content
            except Exception as e:
                res_gpt = f"Error GPT: {str(e)}"

            # 2. CONSULTA GEMINI (Vía API Directa para evitar el Error 404)
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                payload = {"contents": [{"parts": [{"text": p}]}]}
                response = requests.post(gemini_url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    res_gem = response.json()['candidates'][0]['content']['parts'][0]['text']
                else:
                    res_gem = f"Error Gemini {response.status_code}: {response.text}"
            except Exception as e:
                res_gem = f"Error conexión Gemini: {str(e)}"

            # 3. PROCESAMIENTO DE RESULTADOS
            results.append({
                "Prompt": p,
                "Respuesta ChatGPT": res_gpt,
                "Respuesta Gemini": res_gem,
                "Visto en GPT": brand_to_track.lower() in res_gpt.lower(),
                "Visto en Gemini": brand_to_track.lower() in res_gem.lower()
            })
            progress_bar.progress((i + 1) / len(prompts))

        # --- VISUALIZACIÓN DE RESULTADOS ---
        df = pd.DataFrame(results)

        # Métricas de Visibilidad (Share of Voice)
        col1, col2 = st.columns(2)
        with col1:
            gpt_perc = (df["Visto en GPT"].mean() * 100)
            st.metric("Visibilidad en ChatGPT", f"{gpt_perc:.0f}%")
        with col2:
            gem_perc = (df["Visto en Gemini"].mean() * 100)
            st.metric("Visibilidad en Gemini", f"{gem_perc:.0f}%")

        # Tabla de datos
        st.subheader("Detalle del Análisis")
        st.dataframe(df)

        # Descarga
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", csv, "reporte_istobal_ai.csv", "text/csv")

st.divider()
st.caption("Herramienta interna para Istobal. Los datos se consultan en tiempo real a OpenAI y Google.")
