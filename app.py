import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai

# Configuración de la página
st.set_page_config(page_title="Istobal AI Auditor", page_icon="🧼", layout="wide")

st.title("📊 Monitor de Visibilidad IA: ISTOBAL")
st.markdown("Esta herramienta consulta en tiempo real cómo aparece la marca en los principales LLMs.")

# Cargar las APIs desde Secrets de Streamlit
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    # Configurar modelos
    genai.configure(api_key=GEMINI_API_KEY)
    model_gemini = genai.GenerativeModel('gemini-pro')
    client_openai = openai.OpenAI(api_key=OPENAI_API_KEY)
    
except Exception as e:
    st.error("⚠️ Error: No se han encontrado las API Keys en 'Secrets'. Por favor, añádelas en el panel de Streamlit.")
    st.stop()

# Interfaz de entrada
st.sidebar.header("Configuración de Auditoría")
brand_to_track = st.sidebar.text_input("Marca a buscar:", "Istobal")
prompts_raw = st.sidebar.text_area(
    "Introduce tus Prompts (uno por línea):",
    "¿Quiénes son los líderes en puentes de lavado?\nMejor tecnología de reciclaje de agua para lavaderos\nComparativa Istobal vs WashTec"
)

prompts = [p.strip() for p in prompts_raw.split('\n') if p.strip()]

if st.button("🚀 Ejecutar Auditoría"):
    results = []
    
    with st.spinner("Consultando a los modelos..."):
        for p in prompts:
            # --- CONSULTA CHATGPT (GPT-4o) ---
            try:
                res_gpt = client_openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": p}]
                ).choices[0].message.content
            except:
                res_gpt = "Error en conexión"

            # --- CONSULTA GEMINI ---
            try:
                res_gem = model_gemini.generate_content(p).text
            except:
                res_gem = "Error en conexión"

            # Guardar datos
            results.append({
                "Pregunta": p,
                "Respuesta ChatGPT": res_gpt,
                "Respuesta Gemini": res_gem,
                "Menciona Marca (GPT)": brand_to_track.lower() in res_gpt.lower(),
                "Menciona Marca (Gemini)": brand_to_track.lower() in res_gem.lower()
            })

    # Crear DataFrame
    df = pd.DataFrame(results)

    # --- MÉTRICAS RÁPIDAS ---
    col1, col2 = st.columns(2)
    with col1:
        score_gpt = (df["Menciona Marca (GPT)"].sum() / len(df)) * 100
        st.metric("Presencia en ChatGPT", f"{score_gpt:.0f}%")
    with col2:
        score_gem = (df["Menciona Marca (Gemini)"].sum() / len(df)) * 100
        st.metric("Presencia en Gemini", f"{score_gem:.0f}%")

    # --- TABLA DE RESULTADOS ---
    st.subheader("Detalle de las respuestas")
    st.dataframe(df)

    # Botón de descarga
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Informe Completo (CSV)", csv, "informe_ai_istobal.csv", "text/csv")

st.info("💡 Consejo: Usa prompts técnicos sobre lavado de vehículos para ver si la IA reconoce la autoridad de Istobal.")
