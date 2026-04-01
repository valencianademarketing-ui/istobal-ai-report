import streamlit as st
import pandas as pd
import openai
import requests

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Istobal AI Auditor", layout="wide")
st.title("📊 Monitor de Visibilidad IA: ISTOBAL")

# --- 2. SEGURIDAD ---
if "OPENAI_API_KEY" not in st.secrets or "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ Configura las API Keys en los Secrets de Streamlit.")
    st.stop()

# --- 3. INPUTS ---
brand = st.sidebar.text_input("Marca:", "Istobal")
prompts_text = st.sidebar.text_area("Prompts (uno por línea):", "¿Quién es líder en puentes de lavado?")
prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]

if st.button("🚀 Ejecutar Auditoría"):
    results = []
    client_gpt = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    for p in prompts:
        # --- BLOQUE CHATGPT ---
        try:
            res_gpt = client_gpt.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": p}]
            ).choices[0].message.content
        except Exception as e:
            res_gpt = f"Error GPT: {e}"

        # --- BLOQUE GEMINI (AJUSTE FINAL 2026) ---
        try:
            # Usamos el nombre de modelo exacto para la API gratuita actual
            # Probamos con 'gemini-1.5-flash-latest' que es el alias más compatible
            model_id = "gemini-1.5-flash-latest"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={st.secrets['GEMINI_API_KEY']}"
            
            payload = {"contents": [{"parts": [{"text": p}]}]}
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(url, json=payload, headers=headers)
            res_data = response.json()
            
            if response.status_code == 200:
                res_gem = res_data['candidates'][0]['content']['parts'][0]['text']
            else:
                # Si el 'flash-latest' falla, intentamos el 'gemini-1.5-flash' a secas
                url_alt = url.replace("gemini-1.5-flash-latest", "gemini-1.5-flash")
                response_alt = requests.post(url_alt, json=payload, headers=headers)
                if response_alt.status_code == 200:
                    res_gem = response_alt.json()['candidates'][0]['content']['parts'][0]['text']
                else:
                    res_gem = f"Error Google {response_alt.status_code}: {response_alt.text}"
        except Exception as e:
            res_gem = f"Error de red: {e}"

        results.append({
            "Prompt": p,
            "ChatGPT": res_gpt,
            "Gemini": res_gem,
            "Presencia Marca": brand.lower() in res_gpt.lower() or brand.lower() in res_gem.lower()
        })

    st.dataframe(pd.DataFrame(results), use_container_width=True)
