"""Send the Phenix Infinity reminder that is due at the current local time.

This script is intentionally dependency-free so GitHub Actions can run it on
the public repository's free runner without installing the whole application.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, time
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/Santiago")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


ALERTS = {
    time(5, 30): "⏰ **05:30 AM - Ejercicio**\n\nHora de iniciar tu rutina de ejercicio. ¡A darle con todo a la salud! 💪🏋️",
    time(6, 30): "🐶 **06:30 AM - Paseo de tu mascota**\n\nMomento del paseo de 20-30 minutos con tu perro.",
    time(7, 30): "🎬 **07:30 AM - CapCut / Edición**\n\nComienza tu bloque de aprendizaje y el primer Pomodoro.",
    time(9, 30): "🥖 **09:30 AM - Producción de panadería**\n\nHora de comenzar masas, amasado y horneado.",
    time(11, 30): "🥗 **11:30 AM - Sugerencia de almuerzo KETO**\n\n{recipe}\n\n¡Tu almuerzo es a las 12:00 PM!",
    time(13, 30): "💼 **01:30 PM - Negocios y pizzería**\n\nComienza tu bloque de aprendizaje y emprendimiento.",
    time(15, 0): "🦉 **03:00 PM - Duolingo / Idiomas**\n\nMomento de tu lección diaria de 30 minutos.",
    time(16, 0): "🚨 **04:00 PM - Alerta de masas**\n\nSaca las masas de la refrigeradora para que alcancen temperatura ambiente.",
    time(17, 0): "🔥 **05:00 PM - Encender horno**\n\nEnciende el horno para el precalentamiento antes de abrir.",
    time(18, 0): "🍕 **06:00 PM - Apertura de la pizzería**\n\n¡Éxito en las ventas de hoy!",
    time(22, 30): "📋 **10:30 PM - Formulario de producción**\n\nRegistra los panes y pizzas de mañana en el panel web.",
    time(23, 0): "😴 **11:00 PM - Cierre de jornada**\n\n¡Excelente trabajo hoy! Mañana comenzamos a las 05:30 AM.",
}


def post_json(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def keto_recipe() -> str:
    if not GEMINI_API_KEY:
        return "Pollo salteado con aguacate, espinaca, queso y mantequilla."

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={urllib.parse.quote(GEMINI_API_KEY)}"
    )
    payload = {
        "contents": [{"parts": [{"text": (
            "Sugiere una receta keto sencilla para hoy usando huevos, aguacate, "
            "pollo, queso, mantequilla y espinaca. Responde en español en máximo 80 palabras."
        )}]}]
    }
    try:
        result = post_json(url, payload)
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as error:
        print(f"Gemini no disponible, usando receta de respaldo: {error}")
        return "Pollo salteado con aguacate, espinaca, queso y mantequilla."


def send_message(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        raise SystemExit("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en GitHub Secrets.")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    result = post_json(url, {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    if not result.get("ok"):
        raise SystemExit(f"Telegram rechazó el mensaje: {result}")


def main() -> None:
    if os.environ.get("TEST_ALERT", "").lower() == "true":
        send_message("✅ **Phenix Infinity está funcionando**\n\nEste es un mensaje de prueba enviado automáticamente por GitHub.")
        print("Mensaje de prueba enviado.")
        return

    now = datetime.now(TZ)
    due_alert = next(
        (alert for alert_time, alert in ALERTS.items()
         if 0 <= (now.hour * 60 + now.minute) - (alert_time.hour * 60 + alert_time.minute) < 5),
        None,
    )
    if not due_alert:
        print(f"Sin alerta pendiente a las {now:%H:%M} ({TZ.key}).")
        return

    text = due_alert.format(recipe=keto_recipe())
    send_message(text)
    print(f"Alerta enviada a las {now:%H:%M} ({TZ.key}).")


if __name__ == "__main__":
    main()
