import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Istobal AI Auditor", layout="wide", page_icon="📊")
st.title("📊 Auditoría Estratégica: ISTOBAL")

# Configuración de APIs
client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_resource
def get_valid_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for t in ["models/gemini-1.5-flash", "models/gemini-pro"]:
            if t in models: return t
        return models[0]
    except: return "gemini-1.5-flash"

target_model = get_valid_model()

# --- 2. INTERFAZ LATERAL ---
with st.sidebar:
    st.header("Configuración")
    brand = st.text_input("Marca objetivo:", "Istobal")
    
    st.subheader("Prompts por Tipología")
    st.markdown("""
    Escribe los prompts con este formato:  
    `Categoría: Pregunta`
    """)
    default_prompts = (
        "Producto: ¿Qué ventajas tiene el puente de lavado M'NEX32?\n"
        "Tecnología: ¿Qué es el sistema Smartwash?\n"
        "Competencia: ¿Quién es el principal rival de Washtec?\n"
        "Sostenibilidad: ¿Qué empresas de lavado reciclan agua?"
    )
    prompts_raw = st.text_area("Lista de prompts:", default_prompts, height=200)
    
# --- 3. PROCESAMIENTO ---
if st.button("🚀 Ejecutar Auditoría Completa"):
    prompts_list = [p.strip() for p in prompts_raw.split('\n') if ":" in p]
    
    if not prompts_list:
        st.warning("Asegúrate de usar el formato 'Categoría: Pregunta'")
    else:
        results = []
        progress = st.progress(0)
        model_gemini = genai.GenerativeModel(target_model)

        for i, line in enumerate(prompts_list):
            # Separar categoría y pregunta
            tipo, pregunta = line.split(":", 1)
            tipo, pregunta = tipo.strip(), pregunta.strip()
            
            # Consulta ChatGPT
            try:
                res_gpt = client_gpt.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": pregunta}]
                ).choices[0].message.content
            except: res_gpt = "Error"

            # Pausa breve para Gemini
            time.sleep(2)

            # Consulta Gemini
            try:
                res_gem = model_gemini.generate_content(pregunta).text
            except: res_gem = "Error"

            # Evaluar visibilidad
            v_gpt = "✅" if brand.lower() in res_gpt.lower() else "❌"
            v_gem = "✅" if brand.lower() in res_gem.lower() else "❌"

            results.append({
                "Tipología": tipo,
                "Pregunta": pregunta,
                "Presencia GPT": v_gpt,
                "Presencia Gemini": v_gem,
                "Detalle GPT": res_gpt[:200] + "...", # Resumen corto para la tabla
                "Detalle Gemini": res_gem[:200] + "..."
            })
            progress.progress((i + 1) / len(prompts_list))

        # --- 4. VISUALIZACIÓN ---
        df = pd.DataFrame(results)
        
        # Tabla resumen limpia
        st.subheader("Resumen de Visibilidad por Categoría")
        st.dataframe(
            df[["Tipología", "Pregunta", "Presencia GPT", "Presencia Gemini"]],
            use_container_width=True
        )

        # Análisis por tipología
        st.divider()
        st.subheader("Análisis Detallado")
        for tipo in df["Tipología"].unique():
            with st.expander(f"Ver detalles de: {tipo}"):
                sub_df = df[df["Tipología"] == tipo]
                for _, row in sub_df.iterrows():
                    st.markdown(f"**Pregunta:** {row['Pregunta']}")
                    c1, c2 = st.columns(2)
                    c1.info(f"**ChatGPT:**\n\n{row['Detalle GPT']}")
                    c2.success(f"**Gemini:**\n\n{row['Detalle Gemini']}")
                    st.divider()

        # Descarga
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Informe Completo", csv, "auditoria_istobal.csv", "text/csv")
