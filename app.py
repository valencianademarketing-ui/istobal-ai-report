import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Istobal AI Auditor", layout="wide", page_icon="🧼")

st.title("📊 Monitor de Visibilidad IA: ISTOBAL")
st.markdown("Comparativa de respuestas en tiempo real entre OpenAI y Google Gemini.")

# --- 2. CARGA Y CONFIGURACIÓN DE APIS ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ Faltan las claves en 'Secrets'. Por favor, añádelas en el panel de Streamlit Cloud.")
    st.stop()

# Inicializar clientes
client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. INTERFAZ LATERAL ---
st.sidebar.header("Configuración de Auditoría")
brand_name = st.sidebar.text_input("Marca a monitorizar:", "Istobal")
prompts_text = st.sidebar.text_area(
    "Prompts (uno por línea):", 
    "¿Quién lidera el sector de lavado industrial?\nVentajas de la tecnología Smartwash de Istobal"
)

# Procesar lista de prompts
prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]

# Función para obtener el modelo disponible (Caché para evitar re-consultas)
@st.cache_resource
def detect_available_model():
    try:
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Preferimos 2.0, luego 1.5, luego lo que haya
        for m in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
            if any(m in name for name in modelos):
                return m
        return modelos[0] if modelos else "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash"

selected_model = detect_available_model()
st.sidebar.info(f"Modelo Google detectado: {selected_model}")

# --- 4. LÓGICA DE EJECUCIÓN ---
if st.button("🚀 Iniciar Auditoría"):
    if not prompts:
        st.warning("Escribe al menos un prompt para analizar.")
    else:
        results = []
        progress_bar = st.progress(0)
        
        # Instanciar el modelo de Google
        model_google = genai.GenerativeModel(selected_model)

        for i, p in enumerate(prompts):
            # A. CONSULTA OPENAI
            try:
                res_gpt = client_gpt.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": p}]
                ).choices[0].message.content
            except Exception as e:
                res_gpt = f"Error OpenAI: {str(e)}"

            # PAUSA TÉCNICA (Evita el Error 429 de cuota en Google)
            if i > 0:
                time.sleep(2)

            # B. CONSULTA GOOGLE GEMINI
            try:
                response = model_google.generate_content(p)
                res_gem = response.text
            except Exception as e:
                if "429" in str(e):
                    res_gem = "⚠️ Error 429: Cuota excedida. Google pide esperar un minuto."
                else:
                    res_gem = f"Error Gemini: {str(e)}"

            # C. GUARDAR RESULTADOS
            results.append({
                "Pregunta": p,
                "Respuesta ChatGPT": res_gpt,
                "Respuesta Gemini": res_gem,
                "Menciona a la Marca": brand_name.lower() in res_gpt.lower() or brand_name.lower() in res_gem.lower()
            })
            
            # Actualizar barra de progreso
            progress_bar.progress((i + 1) / len(prompts))

        # --- 5. VISUALIZACIÓN DE RESULTADOS ---
        df = pd.DataFrame(results)
        
        # Métricas rápidas
        c1, c2 = st.columns(2)
        with c1:
            gpt_vis = df["Respuesta ChatGPT"].str.contains(brand_name, case=False).sum()
            st.metric("Menciones en ChatGPT", f"{gpt_vis}/{len(prompts)}")
        with c2:
            gem_vis = df["Respuesta Gemini"].str.contains(brand_name, case=False).sum()
            st.metric("Menciones en Gemini", f"{gem_vis}/{len(prompts)}")

        st.divider()
        st.subheader("Detalle de las respuestas")
        st.dataframe(df, use_container_width=True)

        # Exportación
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte CSV",
            data=csv,
            file_name=f"auditoria_ia_{brand_name.lower()}.csv",
            mime="text/csv"
        )

st.divider()
st.caption("Istobal AI Auditor Tool - 2026. Basado en modelos GPT-4o y Gemini Flash.")
