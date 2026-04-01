import streamlit as st
import pandas as pd
import openai
import google.generativeai as genai

# ... (Configuración inicial igual) ...

if st.button("🚀 Ejecutar Auditoría"):
    results = []
    
    # --- DETECCIÓN DE MODELO ACTIVO ---
    # En 2026, intentamos primero los modelos de nueva generación
    try:
        modelos_disponibles = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Prioridad: 1. Gemini 2.0 (Estable) -> 2. Gemini 1.5 (Legacy) -> 3. El primero que haya
        if any("gemini-2.0-flash" in m for m in modelos_disponibles):
            target_model = "gemini-2.0-flash"
        elif any("gemini-1.5-flash" in m for m in modelos_disponibles):
            target_model = "gemini-1.5-flash"
        else:
            target_model = modelos_disponibles[0] if modelos_disponibles else "gemini-pro"
            
        model_gemini = genai.GenerativeModel(target_model)
        st.success(f"Conectado a Google vía: {target_model}")
    except Exception as e:
        st.error(f"No se pudieron listar modelos: {e}")
        st.stop()

    for p in prompts:
        # --- GPT-4o ---
        try:
            res_gpt = client_gpt.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": p}]
            ).choices[0].message.content
        except Exception as e:
            res_gpt = f"Error GPT: {e}"

        # --- GEMINI ---
        try:
            # Forzamos el uso de la versión de producción v1 mediante el SDK
            response = model_gemini.generate_content(p)
            res_gem = response.text
        except Exception as e:
            res_gem = f"Error Gemini ({target_model}): {e}"

        results.append({
            "Prompt": p,
            "ChatGPT": res_gpt,
            "Gemini": res_gem,
            "Visto": brand.lower() in res_gpt.lower() or brand.lower() in res_gem.lower()
        })

    st.dataframe(pd.DataFrame(results), use_container_width=True)
