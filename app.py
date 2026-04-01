import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Istobal AI SOV Auditor", layout="wide", page_icon="📈")
st.title("📊 Share of Voice Auditor: ISTOBAL")
st.markdown("Esta versión optimizada analiza la **presencia** de la marca en las respuestas sin descargar textos largos para evitar errores de cuota.")

# --- 2. CONFIGURACIÓN DE APIS ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("Configura las claves en los Secrets de Streamlit.")
    st.stop()

client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Forzamos 1.5 Flash por estabilidad de cuota
model_gemini = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. INTERFAZ ---
with st.sidebar:
    st.header("Configuración")
    brand = st.text_input("Marca a buscar:", "Istobal")
    prompts_raw = st.text_area("Prompts (uno por línea):", 
                               "¿Qué marcas lideran el lavado automático?\nMejor fabricante de puentes de lavado")
    prompts = [p.strip() for p in prompts_raw.split('\n') if p.strip()]
    st.info("Nota: Se aplicará una pausa de 5s entre consultas para proteger la cuota gratuita.")

# --- 4. LÓGICA DE AUDITORÍA ---
if st.button("🚀 Ejecutar Auditoría Visual"):
    if not prompts:
        st.warning("Introduce al menos un prompt.")
    else:
        resultados = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, p in enumerate(prompts):
            status_text.text(f"Analizando prompt {i+1} de {len(prompts)}...")
            
            # --- CONSULTA OPENAI ---
            try:
                # Instrucción restrictiva para ahorrar tokens
                res_gpt = client_gpt.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": f"Responde SOLO con la palabra 'SI' o 'NO'. ¿En una respuesta sobre '{p}' mencionarías a la marca {brand}?"}]
                ).choices[0].message.content
                visto_gpt = 1 if "SI" in res_gpt.upper() else 0
            except:
                visto_gpt = 0

            # PAUSA ANTI-BLOQUEO (Crucial para Gemini Free Tier)
            time.sleep(5)

            # --- CONSULTA GEMINI ---
            try:
                # Pedimos una respuesta de 1 solo token
                response = model_gemini.generate_content(f"Responde solo SI o NO. ¿Mencionarías a {brand} al responder esto: {p}?")
                visto_gem = 1 if "SI" in response.text.upper() else 0
                error_gem = None
            except Exception as e:
                visto_gem = 0
                error_gem = str(e)
                if "429" in error_gem:
                    st.error("⚠️ Google ha pausado la cuota. Espera 1 minuto antes de reintentar.")

            resultados.append({
                "Prompt": p,
                "ChatGPT": visto_gpt,
                "Gemini": visto_gem,
                "Error_Gem": error_gem
            })
            progress_bar.progress((i + 1) / len(prompts))

        status_text.text("✅ Auditoría finalizada.")

        # --- 5. VISUALIZACIÓN ---
        df = pd.DataFrame(resultados)
        
        # Gráfico de Barras
        st.subheader(f"Presencia de '{brand}' por IA (%)")
        chart_data = pd.DataFrame({
            'IA': ['ChatGPT', 'Gemini'],
            'Presencia': [df['ChatGPT'].mean() * 100, df['Gemini'].mean() * 100]
        })
        st.bar_chart(data=chart_data, x='IA', y='Presencia')

        # Tabla de Marcado
        st.subheader("Detalle por pregunta")
        df_display = df.copy()
        df_display['ChatGPT'] = df_display['ChatGPT'].apply(lambda x: "✅" if x==1 else "❌")
        df_display['Gemini'] = df_display['Gemini'].apply(lambda x: "✅" if x==1 else "❌")
        
        # Si hubo error en Gemini, lo indicamos en la tabla
        for idx, row in df.iterrows():
            if row['Error_Gem']:
                df_display.at[idx, 'Gemini'] = "⚠️ ERROR"

        st.table(df_display[['Prompt', 'ChatGPT', 'Gemini']])

st.divider()
st.caption("Estrategia: Minimización de tokens de salida para evitar Error 429.")
