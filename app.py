import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="AI Competitive Auditor", layout="wide", page_icon="⚔️")
st.title("⚔️ Auditoría Competitiva IA: ISTOBAL vs Competencia")

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

# --- 2. INTERFAZ LATERAL ---
with st.sidebar:
    st.header("Configuración de Marcas")
    brand_main = st.text_input("Marca Principal:", "Istobal")
    competitors_raw = st.text_input("Competidores (separados por coma):", "WashTec, Christ, Ceccato, Tammermatic")
    competitors = [c.strip() for c in competitors_raw.split(",") if c.strip()]
    
    st.subheader("Bloques de Auditoría")
    default_text = (
        "Túneles: ¿Qué túnel de lavado me recomendáis que aguante mucha caña y pase muchos coches por hora?\n"
        "Puentes: Estoy buscando un puente de lavado que sea rápido pero que deje el coche bien seco, ¿cuál es el mejor?\n"
        "Químicos: ¿Qué champús y ceras dan mejor resultado y más brillo en máquinas de lavado automático?\n"
        "Negocio: ¿Realmente sale a cuenta cambiar mi puente de lavado viejo por uno nuevo?\n"
        "Negocio: He oído hablar de lo de Smartwash, ¿qué es exactamente y cómo me ayuda?"
    )
    prompts_raw = st.text_area("Prompts (Categoría: Pregunta):", default_text, height=300)

# --- 3. LÓGICA DE AUDITORÍA ---
if st.button("🚀 Lanzar Auditoría Comparativa"):
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
            
            # Consultas
            try:
                r_gpt = client_gpt.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": q}]).choices[0].message.content
            except: r_gpt = "Error"
            
            time.sleep(2) 
            
            try:
                r_gem = model_gemini.generate_content(q).text
            except: r_gem = "Error"

            # Función de detección
            def check_mentions(text):
                found = []
                if brand_main.lower() in text.lower(): found.append(brand_main)
                for comp in competitors:
                    if comp.lower() in text.lower(): found.append(comp)
                return found

            mentions_gpt = check_mentions(r_gpt)
            mentions_gem = check_mentions(r_gem)

            results.append({
                "Categoría": cat,
                "Pregunta": q,
                "Istobal_GPT": 1 if brand_main in mentions_gpt else 0,
                "Istobal_Gem": 1 if brand_main in mentions_gem else 0,
                "Menciones_GPT": ", ".join(mentions_gpt) if mentions_gpt else "Ninguna",
                "Menciones_Gem": ", ".join(mentions_gem) if mentions_gem else "Ninguna",
                "Texto_GPT": r_gpt,
                "Texto_Gem": r_gem
            })
            progress.progress((i + 1) / len(prompts_list))

        # --- 4. RESULTADOS Y GRÁFICOS ---
        df = pd.DataFrame(results)

        st.subheader("📈 Cuota de Recomendación (Share of Voice)")
        
        # Preparar datos para gráfico: Cuántas veces aparece cada marca en total
        all_mentions = []
        for _, row in df.iterrows():
            all_mentions.extend(row["Menciones_GPT"].split(", "))
            all_mentions.extend(row["Menciones_Gem"].split(", "))
        
        # Limpiar "Ninguna" y contar
        all_mentions = [m for m in all_mentions if m != "Ninguna"]
        if all_mentions:
            mention_counts = pd.Series(all_mentions).value_counts()
            st.bar_chart(mention_counts)
        else:
            st.info("No se detectaron menciones de las marcas configuradas.")

        # Tabla comparativa
        st.subheader("Detalle de la Batalla por el Prompt")
        df_display = df.copy()
        # Estilo visual para la tabla
        st.dataframe(df_display[["Categoría", "Pregunta", "Menciones_GPT", "Menciones_Gem"]], use_container_width=True)

        # Análisis Cualitativo
        with st.expander("🔍 Ver donde gana la competencia"):
            for _, row in df.iterrows():
                if row["Istobal_GPT"] == 0 or row["Istobal_Gem"] == 0:
                    st.write(f"**Alerta en:** {row['Pregunta']}")
                    st.write(f"👉 GPT menciona a: *{row['Menciones_GPT']}*")
                    st.write(f"👉 Gemini menciona a: *{row['Menciones_Gem']}*")
                    st.divider()

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Informe Competitivo", csv, "analisis_competencia_istobal.csv", "text/csv")
