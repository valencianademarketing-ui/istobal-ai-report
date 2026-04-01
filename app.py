import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Istobal AI Strategic Auditor", layout="wide")
st.title("🛡️ Auditoría de Posicionamiento: ISTOBAL")

# Inicialización APIs
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

# --- INTERFAZ ---
with st.sidebar:
    brand = st.text_input("Marca Objetivo:", "Istobal")
    st.subheader("Configuración de Auditoría")
    
    # Pre-cargamos los prompts sugeridos
    default_text = (
        "Producto: ¿Cuál es el mejor puente de lavado para poco espacio?\n"
        "Producto: ¿Qué fabricante tiene los mejores aspiradores de monedas?\n"
        "Producto: Ventajas del sistema touchless frente a cepillos\n"
        "Negocio: ¿Cómo rentabilizar un lavadero de coches?\n"
        "Negocio: Impacto del IoT en la gestión de centros de lavado\n"
        "Negocio: ¿Cómo reducir el consumo de agua en un car wash?"
    )
    prompts_raw = st.text_area("Listado de Prompts (Categoría: Pregunta):", default_text, height=300)

# --- PROCESAMIENTO ---
if st.button("🚀 Iniciar Auditoría por Bloques"):
    prompts_list = [p.strip() for p in prompts_raw.split('\n') if ":" in p]
    
    if not prompts_list:
        st.error("Formato incorrecto. Usa 'Categoría: Pregunta'")
    else:
        results = []
        progress = st.progress(0)
        model_gemini = genai.GenerativeModel(target_model)

        for i, line in enumerate(prompts_list):
            cat, q = line.split(":", 1)
            cat, q = cat.strip(), q.strip()
            
            # Consultas (con manejo de errores y esperas)
            try:
                r_gpt = client_gpt.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": q}]).choices[0].message.content
            except: r_gpt = "Error"
            
            time.sleep(2) # Pausa anti-bloqueo
            
            try:
                r_gem = model_gemini.generate_content(q).text
            except: r_gem = "Error"

            # Evaluación de mención
            m_gpt = 1 if brand.lower() in r_gpt.lower() else 0
            m_gem = 1 if brand.lower() in r_gem.lower() else 0

            results.append({
                "Categoría": cat,
                "Pregunta": q,
                "GPT": m_gpt,
                "Gemini": m_gem,
                "Respuesta GPT": r_gpt,
                "Respuesta Gemini": r_gem
            })
            progress.progress((i + 1) / len(prompts_list))

        # --- RESULTADOS ---
        df = pd.DataFrame(results)

        # Gráfico por categorías
        st.subheader("Share of Voice por Bloque")
        resumen_cat = df.groupby("Categoría")[["GPT", "Gemini"]].mean() * 100
        st.bar_chart(resumen_cat)

        # Tabla Desglosada
        st.subheader("Desglose de Auditoría")
        df_view = df.copy()
        df_view["GPT"] = df_view["GPT"].map({1: "✅", 0: "❌"})
        df_view["Gemini"] = df_view["Gemini"].map({1: "✅", 0: "❌"})
        st.dataframe(df_view[["Categoría", "Pregunta", "GPT", "Gemini"]], use_container_width=True)

        # Detalles
        with st.expander("Ver respuestas completas"):
            for _, row in df.iterrows():
                st.markdown(f"**[{row['Categoría']}] {row['Pregunta']}**")
                c1, c2 = st.columns(2)
                c1.caption("Respuesta ChatGPT")
                c1.write(row["Respuesta GPT"][:500] + "...")
                c2.caption("Respuesta Gemini")
                c2.write(row["Respuesta Gemini"][:500] + "...")
                st.divider()
