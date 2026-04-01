import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

st.set_page_config(page_title="Istobal AI Auditor", layout="wide")
st.title("📊 Cuadro de Mando de Visibilidad: ISTOBAL")

# Configuración de APIs
client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model_gemini = genai.GenerativeModel('gemini-1.5-flash')

# Interfaz
brand = st.sidebar.text_input("Marca:", "Istobal")
prompts_raw = st.sidebar.text_area("Prompts (uno por línea):", "¿Quién lidera el sector de lavado industrial?\nMejores túneles de lavado 2026")
prompts = [p.strip() for p in prompts_raw.split('\n') if p.strip()]

if st.button("🚀 Analizar"):
    if not prompts:
        st.error("Escribe al menos un prompt.")
    else:
        resultados = []
        bar = st.progress(0)

        for i, p in enumerate(prompts):
            # 1. Consulta OpenAI (Instrucción restrictiva para ahorrar tokens)
            try:
                res_gpt = client_gpt.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": f"{p}. Responde solo con SÍ si mencionas a {brand} o NO si no lo mencionas."}]
                ).choices[0].message.content
                visto_gpt = 1 if "SÍ" in res_gpt.upper() else 0
            except:
                visto_gpt = 0

            # Pausa de seguridad
            time.sleep(5)

            # 2. Consulta Gemini (Instrucción restrictiva)
            try:
                # Pedimos una respuesta ultra corta para no quemar la cuota
                response = model_gemini.generate_content(f"{p}. Responde solo la palabra SÍ si mencionas a {brand} o NO si no.")
                visto_gem = 1 if "SÍ" in response.text.upper() else 0
            except:
                visto_gem = 0

            resultados.append({
                "Prompt": p,
                "ChatGPT": visto_gpt,
                "Gemini": visto_gem
            })
            bar.progress((i + 1) / len(prompts))

        # --- GENERACIÓN DE GRÁFICOS ---
        df = pd.DataFrame(resultados)
        
        st.subheader("Porcentaje de Aparición (Share of Voice)")
        
        # Calculamos totales para el gráfico
        chart_data = pd.DataFrame({
            'IA': ['ChatGPT', 'Gemini'],
            'Presencia (%)': [df['ChatGPT'].mean() * 100, df['Gemini'].mean() * 100]
        })
        
        st.bar_chart(data=chart_data, x='IA', y='Presencia (%)')

        # Tabla resumen simple (sin textos largos)
        st.subheader("¿Aparece la marca?")
        df_visual = df.copy()
        df_visual['ChatGPT'] = df_visual['ChatGPT'].map({1: "✅ SÍ", 0: "❌ NO"})
        df_visual['Gemini'] = df_visual['Gemini'].map({1: "✅ SÍ", 0: "❌ NO"})
        st.table(df_visual)
