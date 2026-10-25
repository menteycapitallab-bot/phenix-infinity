from typing import List, Dict
from sqlalchemy.orm import Session
from database.models import InventoryItem, DailyProduction

# Estándares de consumo de materia prima por unidad para panadería venezolana y pizzería
PRODUCT_INGREDIENT_MAP = {
    # Panadería Venezolana
    "cachitos": {"Harina": 0.07, "Mantequilla/Agua": 0.04, "Levadura": 0.002, "Jamón": 0.05, "Queso": 0.02},
    "panes_piñitas": {"Harina": 0.035, "Mantequilla/Agua": 0.02, "Levadura": 0.001, "Azúcar": 0.008},
    "panes_de_queso": {"Harina": 0.06, "Agua/Leche": 0.035, "Levadura": 0.002, "Queso": 0.04},
    
    # Tequeños y Pastelitos
    "tequeños_grandes": {"Harina": 0.03, "Mantequilla": 0.015, "Queso Blanco": 0.04},
    "pastelitos_grandes": {"Harina": 0.035, "Mantequilla": 0.015, "Relleno (Carne/Pollo/Queso)": 0.04},
    "pasapalos": {"Harina": 0.15, "Mantequilla": 0.06, "Queso/Relleno": 0.18}, # Por docena
    
    # Pizzería
    "pizza_familiar": {"Harina": 0.15, "Agua": 0.09, "Levadura": 0.003, "Queso Mozzarella": 0.15, "Salsa de Tomate": 0.10},
    "pizza_personal": {"Harina": 0.09, "Agua": 0.055, "Levadura": 0.002, "Queso Mozzarella": 0.08, "Salsa de Tomate": 0.05},
    
    # Panes Clásicos
    "baguette": {"Harina": 0.13, "Agua": 0.08, "Levadura": 0.003}
}

class InventoryService:
    def calculate_required_ingredients(self, production_data: Dict[str, int]) -> Dict[str, float]:
        """Calcula la materia prima total necesaria según la producción planificada (en kg/litros)."""
        required = {}
        for product_key, qty in production_data.items():
            if qty <= 0:
                continue
            
            key_clean = product_key.lower().replace(" ", "_")
            ingredients = PRODUCT_INGREDIENT_MAP.get(key_clean, {
                "Harina": 0.05 * qty,
                "Materia Prima": 0.03 * qty
            })

            for ing_name, amount_per_unit in ingredients.items():
                total_needed = amount_per_unit * qty
                required[ing_name] = required.get(ing_name, 0.0) + total_needed
        
        return {k: round(v, 3) for k, v in required.items()}

    def check_and_generate_shopping_list(self, db: Session, production_data: Dict[str, int]) -> str:
        """Compara la materia prima requerida contra el inventario actual y genera la lista de compras."""
        required = self.calculate_required_ingredients(production_data)
        missing_items = []
        summary_lines = []

        summary_lines.append("📋 **Consumo Estimado de Materia Prima:**")
        for ing, req_amount in required.items():
            summary_lines.append(f"• **{ing}:** {req_amount} kg/L")

            stock_item = db.query(InventoryItem).filter(InventoryItem.name.ilike(f"%{ing}%")).first()
            current_stock = stock_item.quantity if stock_item else 0.0

            if current_stock < req_amount:
                shortage = round(req_amount - current_stock, 2)
                summary_lines.append(f"   ⚠️ *Faltante:* {shortage} {stock_item.unit if stock_item else 'kg/L'} (Stock: {current_stock})")
                missing_items.append(f"🛒 **{ing}:** Comprar al menos **{shortage} {stock_item.unit if stock_item else 'kg/L'}**")

        if missing_items:
            summary_lines.append("\n🚨 **LISTA DE COMPRAS DE INSUMOS FALTANTES:**")
            summary_lines.extend(missing_items)
        else:
            summary_lines.append("\n✅ **¡Tienes suficiente materia prima en inventario para la producción de mañana!**")

        return "\n".join(summary_lines)

inventory_service = InventoryService()
