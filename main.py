import asyncio
import datetime
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import config
from database.db import init_db, get_db
from database.models import DailyProduction
from services.inventory_service import inventory_service
from scheduler.cron_jobs import setup_scheduler
from bot.main import create_telegram_app

# Rutas absolutas para funcionar tanto localmente como en Render
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "webapp" / "static"
TEMPLATES_DIR = BASE_DIR / "webapp" / "templates"

telegram_bot_app = None
BOT_STARTED = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la app con lifespan (reemplaza on_event deprecated)."""
    global telegram_bot_app, BOT_STARTED
    
    print("[STARTUP]: Inicializando base de datos SQLite...")
    init_db()

    if not BOT_STARTED:
        print("[STARTUP]: Inicializando Telegram Bot App...")
        telegram_bot_app = create_telegram_app()
        
        if telegram_bot_app:
            try:
                await telegram_bot_app.initialize()
                await telegram_bot_app.start()
                # Iniciar Polling de Telegram en segundo plano
                asyncio.create_task(telegram_bot_app.updater.start_polling())
                print("[STARTUP]: Telegram Bot Polling iniciado exitosamente.")
            except Exception as e:
                print(f"[STARTUP ERROR Bot]: {e}")

            try:
                # Iniciar Scheduler de Alertas y Cron Jobs
                print("[STARTUP]: Inicializando Motor Scheduler (APScheduler)...")
                setup_scheduler(telegram_bot_app.bot)
                print("[STARTUP]: Scheduler iniciado. Todas las alertas programadas.")
            except Exception as e:
                print(f"[STARTUP ERROR Scheduler]: {e}")
            
            BOT_STARTED = True
            print("[STARTUP]: Phenix Infinity listo y corriendo 24/7.")

    yield  # La app corre aqui

    # Shutdown limpio
    print("[SHUTDOWN]: Cerrando Phenix Infinity...")
    if telegram_bot_app:
        try:
            await telegram_bot_app.updater.stop()
            await telegram_bot_app.stop()
            await telegram_bot_app.shutdown()
        except Exception as e:
            print(f"[SHUTDOWN ERROR]: {e}")


app = FastAPI(
    title="Phenix Infinity - Asistente Virtual",
    lifespan=lifespan
)

# Archivos estaticos y plantillas con rutas absolutas
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html><head><title>Phenix Infinity</title></head>
    <body style="font-family:Arial;text-align:center;padding:40px;background:#1a1a2e;color:#eee">
    <h1>🔥 Phenix Infinity</h1>
    <p>Asistente Virtual Activo 24/7 — Bot de Telegram, Panaderia y Pizzeria</p>
    <p><a href='/ping' style='color:#00d4ff'>/ping</a> | 
       <a href='/health' style='color:#00d4ff'>/health</a> |
       <a href='/app' style='color:#00d4ff'>/app</a></p>
    </body></html>
    """

@app.get("/ping")
async def ping():
    """Keep-alive para cron-job.org - evita la suspension en Render Free Tier."""
    return {
        "status": "alive",
        "service": "Phenix Infinity",
        "bot_active": BOT_STARTED,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@app.get("/health")
async def health():
    """Health check completo del sistema."""
    return {
        "status": "ok",
        "bot_active": BOT_STARTED,
        "server_time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "server_time_ve": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4))).strftime("%Y-%m-%d %H:%M:%S VET")
    }

@app.get("/app", response_class=HTMLResponse)
async def get_webapp(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        print(f"[WEBAPP ERROR]: {e}")
        return HTMLResponse(
            content="<h1>Phenix Infinity - WebApp</h1><p>Servidor activo. Bot de Telegram funcionando correctamente.</p>",
            status_code=200
        )

@app.post("/api/production")
async def save_production(payload: dict, db: Session = Depends(get_db)):
    """Registra la produccion de manana y calcula la lista de compras de insumos."""
    today_str = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    for prod_name, qty in payload.items():
        if qty > 0:
            prod = DailyProduction(
                date=today_str,
                product_name=prod_name,
                quantity_planned=qty
            )
            db.add(prod)
    db.commit()

    summary_text = inventory_service.check_and_generate_shopping_list(db, payload)

    if telegram_bot_app and config.TELEGRAM_CHAT_ID:
        try:
            await telegram_bot_app.bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=f"📝 **Producción Registrada para Mañana ({today_str}):**\n\n{summary_text}",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Error enviando notificacion de produccion: {e}")

    return JSONResponse({"status": "ok", "summary": summary_text})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=False)
