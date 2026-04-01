import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai

st.title("📊 ISTOBAL - AI Visibility Tracker")

# Configuración en el lateral
with st.sidebar:
    api_gpt = st.text_input("OpenAI API Key", type="password")
    api_gemini = st.text_input("Gemini API Key", type="password")

prompt_input = st.text_area("Introduce tus prompts (uno por línea):", "Sistemas de lavado Istobal")

if st.button("Analizar"):
    # Aquí iría la lógica de consulta (la completaremos en el siguiente paso)
    st.write(f"Analizando: {prompt_input}")
