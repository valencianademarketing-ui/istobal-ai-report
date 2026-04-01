import requests # Añade esto al principio de tu app.py con los otros imports

# --- DENTRO DEL BUCLE FOR, EN LA SECCIÓN DE GEMINI ---
        try:
            # Consulta directa vía API REST (más estable)
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": p}]}]
            }
            response = requests.post(gemini_url, json=payload)
            response_json = response.json()
            
            if response.status_code == 200:
                res_gem = response_json['candidates'][0]['content']['parts'][0]['text']
            else:
                res_gem = f"Error {response.status_code}: {response_json.get('error', {}).get('message', 'Desconocido')}"
        except Exception as e:
            res_gem = f"Error de conexión: {str(e)}"
