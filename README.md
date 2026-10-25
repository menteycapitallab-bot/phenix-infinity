# PHENIX INFINITY

Asistente virtual 24/7 con agenda diaria, alertas por Telegram, recetas Keto, Panadería y Pizzería

## Alertas gratuitas con GitHub Actions

El workflow `Phenix Infinity - alertas` se ejecuta cada cinco minutos en la zona
horaria `America/Santiago` y envía a Telegram la alerta que corresponda. Para
activarlo, configura estos secretos en GitHub en `Settings > Secrets and
variables > Actions`:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `GEMINI_API_KEY` (opcional; se usa una receta de respaldo si falta)

GitHub Actions no mantiene un proceso permanente: ejecuta tareas breves y puede
retrasar una ejecución programada. Para este proyecto básico no necesitamos
Google Cloud ni Render: las alertas se gestionan directamente desde GitHub.

Para enviar un mensaje de prueba, abre el workflow en GitHub, pulsa `Run
workflow` y marca `Enviar un mensaje de prueba a Telegram`.

---
*Proyecto gestionado por Antigravity AI Assistant.*
