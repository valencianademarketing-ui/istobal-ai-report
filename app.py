import streamlit as st
import pandas as pd
import openai
import requests

st.set_page_config(page_title="Istobal AI Auditor", layout="wide")
st.title("📊 Monitor de Visibilidad IA: ISTOBAcccL")

# --- SEGURIDAD ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("Configura las claves en Secrets.")
    st.stop()

brand = st.sidebar.text_input("Marca:", "Istobal")
prompts_text = st.sidebar.text_area("Prompts:", "¿Quién lidera el sector de lavado?")
prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]

if st.button("🚀 Ejecutar"):
    results = []
    client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    for p in prompts:
        # --- GPT-4o ---
        try:
            res_gpt = client_gpt.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": p}]
            ).choices[0].message.content
        except Exception as e:
            res_gpt = f"Error GPT: {e}"

        # --- GEMINI (Bucle de reintentos con diferentes modelos) ---
        res_gem = "No se pudo conectar con ningún modelo de Google."
        # Lista de modelos por orden de probabilidad de éxito en cuenta gratis 2026
        modelos_a_probar = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
        
        for m_id in modelos_a_probar:
            try:
                # URL usando v1 (más estable que v1beta)
                url = f"https://generativelanguage.googleapis.com/v1/models/{m_id}:generateContent?key={st.secrets['GEMINI_API_KEY']}"
                
                # Añadimos Headers de navegador para evitar bloqueos de seguridad
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                payload = {"contents": [{"parts": [{"text": p}]}]}
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    res_gem = response.json()['candidates'][0]['content']['parts'][0]['text']
                    break # Si funciona, salimos del bucle de modelos
                else:
                    res_gem = f"Error {response.status_code} en {m_id}: {response.text}"
            except Exception as e:
                res_gem = f"Error conexión: {e}"

        results.append({
            "Prompt": p,
            "ChatGPT": res_gpt,
            "Gemini": res_gem,
            "Visto": brand.lower() in res_gpt.lower() or brand.lower() in res_gem.lower()
        })

    st.dataframe(pd.DataFrame(results))
