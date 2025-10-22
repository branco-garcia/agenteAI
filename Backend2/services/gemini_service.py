import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def generar_respuesta_gemini(prompt: str) -> str:
    try:
        respuesta = model.generate_content(prompt)
        return respuesta.text.strip()
    except Exception as e:
        return f"❌ Error al generar respuesta: {e}"