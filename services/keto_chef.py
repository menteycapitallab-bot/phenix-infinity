import random
from services.gemini_service import gemini_service

DEFAULT_KETO_RECIPES = [
    """🥗 **Ensalada de Pollo a la Plancha con Aguacate y Bacon**
⏱️ **Tiempo:** 15 minutos
📝 **Ingredientes:** 150g pechuga de pollo, 1/2 aguacate, 2 tiras de bacon crocante, 2 tazas lechuga/espinaca, 2 cdas aceite de oliva.
🍳 **Preparación:** Cocinar el pollo y bacon. Servir sobre lechuga fresca con aguacate en cubos y aliñar con aceite de oliva.
📊 **Macros:** 38g Grasa | 35g Proteína | 4g Carbos Netos.""",

    """🥗 **Pizza Keto en Sartén con Base de Queso y Huevo**
⏱️ **Tiempo:** 15 minutos
📝 **Ingredientes:** 2 huevos, 1 taza queso mozzarella rallado, 2 cdas salsa de tomate baja en azúcar, pepperoni o jamón, orégano.
🍳 **Preparación:** Derretir el queso en sartén antiadherente con los huevos batidos para formar la masa crust. Agregar salsa, topping y gratinar.
📊 **Macros:** 42g Grasa | 28g Proteína | 5g Carbos Netos.""",

    """🥗 **Pechuga Gratinada con Queso Gouda y Champiñones**
⏱️ **Tiempo:** 18 minutos
📝 **Ingredientes:** 180g pechuga de pollo, 50g champiñones laminados, 60g queso gouda, 1 cda mantequilla.
🍳 **Preparación:** Saltear champiñones en mantequilla, sellar la pechuga, cubrir con el salteado y queso hasta fundir.
📊 **Macros:** 36g Grasa | 40g Proteína | 3g Carbos Netos."""
]

class KetoChefService:
    async def get_daily_recipe(self) -> str:
        recipe = await gemini_service.get_keto_recommendation()
        if recipe:
            return recipe
        return random.choice(DEFAULT_KETO_RECIPES)

keto_chef = KetoChefService()
