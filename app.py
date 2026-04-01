import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Istobal AI Auditor", layout="wide", page_icon="🧼")
st.title("📊 Monitor de Visibilidad IA: ISTOBAL")

# --- 2. SEGURIDAD ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("Configura las API Keys en los Secrets de Streamlit.")
    st.stop()

# Inicializar APIs
client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. AUTODETECCIÓN DE MODELO (El truco que funcionó) ---
@st.cache_resource
def get_working_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        prioridades = ["models/gemini-2.0-flash", "models/gemini-1.5-flash", "models/gemini-pro"]
        for p in prioridades:
            if p in available_models: return p
        return available_models[0] if available_models else None
    except:
        return "models/gemini-1.5-flash"

target_model = get_working_model()

# --- 4. INTERFAZ LATERAL ---
brand = st.sidebar.text_input("Marca a buscar:", "Istobal")
prompts_raw = st.sidebar.text_area("Prompts (uno por línea):", "¿Quién fabrica los mejores puentes de lavado?\nTecnología Smartwash de Istobal")
prompts = [p.strip() for p in prompts_raw.split('\n') if p.strip()]

st.sidebar.info(f"Conectado a: {target_model}")

# --- 5. LÓGICA DE EJECUCIÓN (Formato Tabla) ---
if st.button("🚀 Iniciar Auditoría"):
    if not prompts:
        st.warning("Introduce al menos un prompt.")
    else:
        results = []
        progress_bar = st.progress(0)
        model_gemini = genai.GenerativeModel(target_model)

        for i, p in enumerate(prompts):
            # A. CONSULTA CHATGPT
            try:
                res_gpt = client_gpt.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": p}]
                ).choices[0].message.content
            except Exception as e:
                res_gpt = f"Error GPT: {e}"

            # PAUSA DE SEGURIDAD PARA GEMINI (Evita el 429)
            time.sleep(2)

            # B. CONSULTA GEMINI
            try:
                response = model_gemini.generate_content(p)
                res_gem = response.text
            except Exception as e:
                res_gem = f"Error Gemini: {e}"

            # C. GUARDAR EN LISTA PARA LA TABLA
            results.append({
                "Prompt": p,
                "Respuesta ChatGPT": res_gpt,
                "Respuesta Gemini": res_gem,
                "Menciona Marca": brand.lower() in res_gpt.lower() or brand.lower() in res_gem.lower()
            })
            progress_bar.progress((i + 1) / len(prompts))

        # --- 6. MOSTRAR TABLA ---
        df = pd.DataFrame(results)
        
        st.subheader("Resultados del Análisis Comparativo")
        # Mostramos la tabla ocupando todo el ancho
        st.dataframe(df, use_container_width=True)

        # Botón para descargar el reporte
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte CSV para Excel",
            data=csv,
            file_name="auditoria_ia_istobal.csv",
            mime="text/csv"
        )

st.divider()
st.caption("Herramienta interna. Si Gemini falla por cuota, espera 1 minuto y reduce el número de prompts.")
