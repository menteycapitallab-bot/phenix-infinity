from google import genai
from google.genai import types
from config import config

class GeminiService:
    def __init__(self):
        self.model_names = [
            "gemini-3.6-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro"
        ]

    def get_client(self):
        api_key = config.GEMINI_API_KEY
        if not api_key or "TU_GEMINI" in api_key:
            api_key = config.GEMINI_API_KEY
        return genai.Client(api_key=api_key)

    async def generate_text(self, prompt: str) -> str:
        """Envía una consulta de texto a Google Gemini mediante el SDK oficial con fallback de modelos."""
        client = self.get_client()
        if not client:
            return None

        for model in self.model_names:
            try:
                res = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                if res and res.text:
                    return res.text
            except Exception as e:
                print(f"[GeminiService] Error con modelo {model}: {e}")
        return None

    async def generate_from_audio(self, audio_bytes: bytes, prompt: str) -> str:
        """Procesa una nota de voz (audio OGG) directamente con Gemini usando el SDK oficial."""
        client = self.get_client()
        if not client:
            return None

        for model in self.model_names:
            try:
                res = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_bytes(
                            data=audio_bytes,
                            mime_type="audio/ogg"
                        ),
                        prompt
                    ]
                )
                if res and res.text:
                    return res.text
            except Exception as e:
                print(f"Excepción en generate_from_audio con modelo {model}: {e}")
                
                # Fallback intentando sin mime_type explícito si falla el códec
                try:
                    res = client.models.generate_content(
                        model=model,
                        contents=[
                            types.Part.from_bytes(
                                data=audio_bytes,
                                mime_type="audio/mp3"
                            ),
                            prompt
                        ]
                    )
                    if res and res.text:
                        return res.text
                except Exception as ex:
                    print(f"Fallback audio exception con modelo {model}: {ex}")
                    
        return None

    async def get_keto_recommendation(self, ingredients_available: str = "huevos, aguacate, pollo, queso, mantequilla, espinaca") -> str:
        prompt = f"""
Eres un Chef Keto Experto. Sugiere una receta de almuerzo KETO deliciosa, fácil y rápida (menos de 20 minutos de preparación).
Garantiza que la receta tenga menos de 20g de carbohidratos netos.
Ingredientes disponibles en la casa: {ingredients_available}.

Responde en formato Markdown atractivo con:
1. 🥗 **Nombre del Platillo**
2. ⏱️ **Tiempo de preparación**
3. 📝 **Ingredientes**
4. 🍳 **Pasos rápidos**
5. 📊 **Macros aproximados** (Grasas %, Proteínas %, Carbos Netos g).
        """
        response = await self.generate_text(prompt)
        if response:
            return response
        
        return """🥗 **Omelette Keto Especial de Aguacate y Queso**
⏱️ **Tiempo:** 12 minutos
📝 **Ingredientes:** 3 huevos, 50g queso mozzarella, 1/2 aguacate, 1 cda mantequilla, sal y pimienta.
🍳 **Pasos:**
1. Batir los 3 huevos con sal y pimienta.
2. Derretir mantequilla en la sartén a fuego medio.
3. Verter los huevos, agregar el queso rallado y láminas de aguacate.
4. Doblar por la mitad y servir bien caliente.
📊 **Macros:** 35g Grasa | 22g Proteína | 3g Carbos Netos."""

gemini_service = GeminiService()
