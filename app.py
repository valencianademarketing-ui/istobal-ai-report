import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai
import time

st.set_page_config(page_title="Istobal AI Auditor", layout="wide")
st.title("📊 Monitor de Visibilidad IA: ISTOBAL")

# Configuración rápida
client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Usamos el nombre directo que sabemos que te funciona
model_gemini = genai.GenerativeModel('gemini-1.5-flash')

brand = st.sidebar.text_input("Marca:", "Istobal")
prompt_input = st.sidebar.text_area("Introduce tu pregunta:")

if st.button("🚀 Analizar"):
    if not prompt_input:
        st.error("Escribe una pregunta.")
    else:
        # 1. Obtener respuesta de GPT
        try:
            res_gpt = client_gpt.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt_input}]
            ).choices[0].message.content
        except Exception as e:
            res_gpt = f"Error GPT: {e}"

        # 2. Pequeña pausa de 2 segundos (vital para evitar el 429)
        time.sleep(2)

        # 3. Obtener respuesta de Gemini
        try:
            response = model_gemini.generate_content(prompt_input)
            res_gem = response.text
        except Exception as e:
            res_gem = f"Error Gemini (Cuota): {e}"

        # 4. CREAR LA TABLA (Solo con los datos de esta consulta)
        datos = {
            "Modelo": ["ChatGPT (OpenAI)", "Gemini (Google)"],
            "Respuesta": [res_gpt, res_gem],
            "Menciona Marca": [brand.lower() in res_gpt.lower(), brand.lower() in res_gem.lower()]
        }
        
        df = pd.DataFrame(datos)
        
        # Mostramos los resultados
        st.subheader("Comparativa de respuestas")
        st.table(df) # st.table es más ligero que st.dataframe para evitar errores

        # Opcional: Mostrar las respuestas en grande debajo por si la tabla corta el texto
        with st.expander("Ver respuestas completas"):
            st.markdown(f"**ChatGPT:** {res_gpt}")
            st.divider()
            st.markdown(f"**Gemini:** {res_gem}")
