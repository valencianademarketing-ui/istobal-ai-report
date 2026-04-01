import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time
import re

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="AI Competitive Auditor", layout="wide", page_icon="⚔️")
st.title("⚔️ Auditoría Competitiva IA: ISTOBAL")

# --- 2. INICIALIZACIÓN DE APIS ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ Configura las API Keys en los 'Secrets' de Streamlit.")
    st.stop()

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

# --- 3. INTERFAZ LATERAL ---
with st.sidebar:
    st.header("🔍 Configuración")
    brand_main = st.text_input("Marca Principal (Ej: Istobal):", "Istobal")
    competitors_raw = st.text_input("Competidores (separados por coma):", "WashTec, Christ, Ceccato, Karcher")
    
    # Limpiamos la lista de competidores
    competitors = [c.strip() for c in competitors_raw.split(",") if c.strip()]
    
    st.subheader("📝 Bloques de Prompts")
    # Prompts naturales según lo hablado
    default_text = (
        "Túneles: ¿Qué túnel de lavado me recomendáis que aguante mucha caña y pase muchos coches por hora?\n"
        "Puentes: Estoy buscando un puente de lavado que sea rápido pero que deje el coche bien seco, ¿cuál es el mejor?\n"
        "Centros de Lavado: Proveedores de equipos para boxes de lavado a presión\n"
        "Vehículo Industrial: Tengo una flota de camiones y necesito instalar un lavado automático, ¿qué marcas mandan?\n"
        "Químicos: ¿Qué champús y ceras dan mejor resultado y más brillo en máquinas de lavado?\n"
        "Tratamiento Agua: ¿Cómo puedo reciclar el agua de mi lavadero para no gastar tanto?\n"
        "Negocio: ¿Realmente sale a cuenta cambiar mi puente de lavado viejo por uno nuevo?\n"
        "Negocio: He oído hablar de Smartwash, ¿qué es y cómo me ayuda a controlar el negocio?"
    )
    prompts_raw = st.text_area("Prompts (Categoría: Pregunta):", default_text, height=350)

# --- 4. FUNCIÓN DE DETECCIÓN ROBUSTA (Soluciona tu error) ---
def check_mentions(text, main_brand, comp_list):
    found = []
    if not text or "Error" in text:
        return found
    
    # 1. Limpieza total: quitamos asteriscos de negritas, pasamos a minúsculas y quitamos acentos básicos
    clean_text = text.lower().replace("*", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    
    # 2. Comprobar Marca Principal
    target = main_brand.lower().strip()
    if target in clean_text:
        found.append(main_brand)
        
    # 3. Comprobar Competidores
    for comp in comp_list:
        if comp.lower().strip() in clean_text:
            found.append(comp)
            
    return list(set(found)) # Evitar duplicados

# --- 5. EJECUCIÓN ---
if st.button("🚀 Iniciar Auditoría"):
    prompts_list = [p.strip() for p in prompts_raw.split('\n') if ":" in p]
    
    if not prompts_list:
        st.error("Formato incorrecto. Usa 'Categoría: Pregunta'")
    else:
        results = []
        progress = st.progress(0)
        status = st.empty()
        model_gemini = genai.GenerativeModel(target_model)

        for i, line in enumerate(prompts_list):
            cat, q = line.split(":", 1)
            cat, q = cat.strip(), q.strip()
            status.text(f"Analizando: {q}...")
            
            # Consulta ChatGPT
            try:
                r_gpt = client_gpt.chat.completions.create(
                    model="gpt-4o", 
                    messages=[{"role": "user", "content": q}]
                ).choices[0].message.content
            except Exception as e: r_gpt = f"Error GPT: {e}"
            
            time.sleep(2) # Respetar cuota Gemini
            
            # Consulta Gemini
            try:
                r_gem = model_gemini.generate_content(q).text
            except Exception as e: r_gem = f"Error Gemini: {e}"

            # Detección de menciones con la nueva función robusta
            mentions_gpt = check_mentions(r_gpt, brand_main, competitors)
            mentions_gem = check_mentions(r_gem, brand_main, competitors)

            results.append({
                "Categoría": cat,
                "Pregunta": q,
                "Istobal_Presente": 1 if brand_main in (mentions_gpt + mentions_gem) else 0,
                "Menciones GPT": ", ".join(mentions_gpt) if mentions_gpt else "Ninguna",
                "Menciones Gemini": ", ".join(mentions_gem) if mentions_gem else "Ninguna",
                "Respuesta GPT": r_gpt,
                "Respuesta Gemini": r_gem
            })
            progress.progress((i + 1) / len(prompts_list))

        status.success("✅ Auditoría completada")

        # --- 6. VISUALIZACIÓN DE RESULTADOS ---
        df = pd.DataFrame(results)

        # Gráfico de Share of Voice
        st.subheader("📊 Cuota de Aparición por Marca")
        all_mentions = []
        for m in df["Menciones GPT"].tolist() + df["Menciones Gemini"].tolist():
            if m != "Ninguna":
                all_mentions.extend([x.strip() for x in m.split(",")])
        
        if all_mentions:
            counts = pd.Series(all_mentions).value_counts()
            st.bar_chart(counts)
        else:
            st.info("No se detectaron marcas en las respuestas.")

        # Tabla Principal
        st.subheader("📝 Detalle de Menciones")
        st.dataframe(df[["Categoría", "Pregunta", "Menciones GPT", "Menciones Gemini"]], use_container_width=True)

        # Comparativa Visual Expandible
        st.subheader("🔍 Análisis Cualitativo")
        for _, row in df.iterrows():
            with st.expander(f"{row['Categoría']}: {row['Pregunta']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**ChatGPT** (Menciona: `{row['Menciones GPT']}`)")
                    st.write(row["Respuesta GPT"])
                with c2:
                    st.markdown(f"**Gemini** (Menciona: `{row['Menciones Gemini']}`)")
                    st.write(row["Respuesta Gemini"])

        # Descarga de datos
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Informe CSV", csv, "auditoria_ia_competencia.csv", "text/csv")
