import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Istobal AI Auditor", layout="wide")
st.title("📊 Monitor de Visibilidad IA: ISTOBAL")

# --- 2. CARGA DE CLAVES ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("Configura las claves en los Secrets de Streamlit.")
    st.stop()

# Inicializar APIs
client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. INTERFAZ LATERAL ---
brand = st.sidebar.text_input("Marca a buscar:", "Istobal")
prompts_text = st.sidebar.text_area(
    "Prompts (uno por línea):", 
    "¿Quién lidera el sector de lavado industrial?\nVentajas de Smartwash Istobal"
)

# Definir la lista de prompts AQUÍ para evitar el NameError
prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]

# --- 4. DETECCIÓN AUTOMÁTICA DE MODELO ---
@st.cache_resource
def get_best_model():
    try:
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if any("gemini-2.0-flash" in m for m in modelos): return "gemini-2.0-flash"
        if any("gemini-1.5-flash" in m for m in modelos): return "gemini-1.5-flash"
        return modelos[0] if modelos else "gemini-pro"
    except:
        return "gemini-1.5-flash"

target_model_name = get_best_model()
st.sidebar.success(f"Google AI: {target_model_name}")

# --- 5. EJECUCIÓN ---
if st.button("🚀 Iniciar Auditoría"):
    if not prompts:
        st.warning("Escribe algún prompt.")
    else:
        results = []
        model_gemini = genai.GenerativeModel(target_model_name)
        
        bar = st.progress(0)
        for i, p in enumerate(prompts):
            # Consulta GPT
            try:
                res_gpt = client_gpt.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": p}]
                ).choices[0].message.content
            except Exception as e:
                res_gpt = f"Error GPT: {e}"

            # Consulta Gemini
            try:
                response = model_gemini.generate_content(p)
                res_gem = response.text
            except Exception as e:
                res_gem = f"Error Gemini: {e}"

            results.append({
                "Prompt": p,
                "ChatGPT (OpenAI)": res_gpt,
                "Gemini (Google)": res_gem,
                "Menciona Marca": brand.lower() in res_gpt.lower() or brand.lower() in res_gem.lower()
            })
            bar.progress((i + 1) / len(prompts))

        # Mostrar resultados
        df = pd.DataFrame(results)
        st.subheader("Resultados de Visibilidad")
        st.dataframe(df, use_container_width=True)
