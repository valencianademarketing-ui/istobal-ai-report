import streamlit as st
import pandas as pd
import openai
import requests
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Istobal AI Auditor", layout="wide")
st.title("📊 Monitor de Visibilidad IA: ISTOBALio")

# --- VERIFICACIÓN DE CLAVES ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("Configura OPENAI_API_KEY y GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

# --- INTERFAZ ---
brand = st.sidebar.text_input("Marca:", "Istobal")
prompts_text = st.sidebar.text_area("Prompts (uno por línea):", "¿Quién fabrica los mejores túneles de lavado?")
prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]

if st.button("🚀 Analizar"):
    results = []
    client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    for p in prompts:
        # 1. GPT-4o (Suele funcionar siempre si tienes saldo)
        try:
            res_gpt = client_gpt.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": p}]
            ).choices[0].message.content
        except Exception as e:
            res_gpt = f"Error GPT: {e}"

        # 2. GEMINI PRO (El modelo más compatible para API gratuita)
        try:
            # Usamos la URL v1 con el modelo gemini-pro (el clásico)
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={st.secrets['GEMINI_API_KEY']}"
            headers = {'Content-Type': 'application/json'}
            data = {"contents": [{"parts": [{"text": p}]}]}
            
            response = requests.post(url, headers=headers, json=data)
            res_json = response.json()
            
            if response.status_code == 200:
                res_gem = res_json['candidates'][0]['content']['parts'][0]['text']
            else:
                # Si falla, probamos con la versión v1beta por si tu cuenta es muy nueva
                url_beta = url.replace("/v1/", "/v1beta/")
                response = requests.post(url_beta, headers=headers, json=data)
                if response.status_code == 200:
                    res_gem = response.json()['candidates'][0]['content']['parts'][0]['text']
                else:
                    res_gem = f"Error {response.status_code}: {response.text}"
        except Exception as e:
            res_gem = f"Error conexión: {e}"

        results.append({
            "Prompt": p,
            "ChatGPT": res_gpt,
            "Gemini": res_gem,
            "Menciona Marca": brand.lower() in res_gpt.lower() or brand.lower() in res_gem.lower()
        })

    st.table(pd.DataFrame(results))
