import asyncio
import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot
from config import config
from database.db import SessionLocal
import httpx
from database.models import PomodoroLog, DailyProduction
from services.keto_chef import keto_chef

async def job_keep_alive(bot: Bot = None):
    """Auto-ping HTTP cada 10 minutos para evitar que la app en Render entre en modo de suspensión (spin down)."""
    webapp_url = config.WEBAPP_URL
    if webapp_url and "localhost" not in webapp_url and "127.0.0.1" not in webapp_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(webapp_url)
                print(f"[KEEP-ALIVE AUTO PING]: Status {res.status_code} en {webapp_url}")
        except Exception as e:
            print(f"[KEEP-ALIVE PING ERROR]: {e}")


scheduler = AsyncIOScheduler(timezone=ZoneInfo("America/Caracas"))
IS_PAUSED_TODAY = False

def set_paused_status(status: bool):
    global IS_PAUSED_TODAY
    IS_PAUSED_TODAY = status

async def send_telegram_alert(bot: Bot, text: str, reply_markup=None):
    """Envía una notificación al Telegram del usuario."""
    chat_id = config.TELEGRAM_CHAT_ID
    if not chat_id or not bot:
        print(f"[ALERT SKIPPED - NO CHAT ID]: {text}")
        return
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception as e:
        print(f"Error enviando alerta por Telegram: {e}")

# Jobs Programados

async def job_0530_ejercicio(bot: Bot):
    await send_telegram_alert(bot, "⏰ **¡Buenos días! 05:30 AM**\n\nHora de iniciar tu rutina de **Ejercicio** (1 hora). ¡A darle con todo a la salud! 💪🏋️")

async def job_0630_paseo_perro(bot: Bot):
    keyboard = [
        [InlineKeyboardButton("▶️ Iniciar Paseo (30m)", callback_data="start_dog_walk")],
        [InlineKeyboardButton("⏰ Posponer a la tarde (3:30 PM)", callback_data="snooze_dog_walk")]
    ]
    await send_telegram_alert(bot, "🐶 **06:30 AM - Paseo de tu Mascota**\n\n¿Listo para el paseo de 20-30 minutos con tu perro?", reply_markup=InlineKeyboardMarkup(keyboard))

async def job_0730_capcut(bot: Bot):
    keyboard = [
        [InlineKeyboardButton("🍅 Iniciar Pomodoro 1 (25m)", callback_data="pomo_capcut_1")]
    ]
    await send_telegram_alert(bot, "🎬 **07:30 AM - Aprendizaje CapCut / Edición**\n\n¡Hora de tu bloque de estudio de 2 horas! ¿Arrancamos el primer Pomodoro?", reply_markup=InlineKeyboardMarkup(keyboard))

async def job_0930_panaderia(bot: Bot):
    await send_telegram_alert(bot, "🥖 **09:30 AM - Bloque de Producción de Panadería**\n\n4 horas para masas, amasado y horneado de panes. ¡Manos a la obra!")

async def job_1130_receta_keto(bot: Bot):
    recipe = await keto_chef.get_daily_recipe()
    keyboard = [
        [InlineKeyboardButton("🔄 Sugerir Otra Receta Keto", callback_data="keto_refresh")]
    ]
    await send_telegram_alert(bot, f"🥗 **11:30 AM - Sugerencia de Almuerzo KETO**\n\n{recipe}\n\n*¡Tu almuerzo es a las 12:00 PM!*", reply_markup=InlineKeyboardMarkup(keyboard))

async def job_1330_negocios(bot: Bot):
    keyboard = [
        [InlineKeyboardButton("🍅 Iniciar Pomodoro 1 (25m)", callback_data="pomo_business_1")]
    ]
    await send_telegram_alert(bot, "💼 **01:30 PM - Aprendizaje de Negocios y Pizzería**\n\nBloque de 1.5 horas para impulsar tu emprendimiento. ¿Iniciamos Pomodoro?", reply_markup=InlineKeyboardMarkup(keyboard))

async def job_1500_duolingo(bot: Bot):
    await send_telegram_alert(bot, "🦉 **03:00 PM - Duolingo / Idiomas**\n\n¡Momento de tu lección diaria de 30 minutos para no perder tu racha! 🔥")

async def job_1600_masas_critico(bot: Bot):
    if IS_PAUSED_TODAY:
        await send_telegram_alert(bot, "🌧️ **Día en Pausa:** Alerta de sacar masas omitida por el Modo Emergencia/Lluvia.")
        return
    keyboard = [
        [InlineKeyboardButton("✅ MASAS AFUERA", callback_data="confirm_masas")]
    ]
    await send_telegram_alert(bot, "🚨 **04:00 PM - ¡ALERTA CRÍTICA PIZZERÍA!**\n\n⚠️ **DEBES SACAR LAS MASAS DE LA REFRIGERADORA YA** para que alcancen la temperatura ambiente antes de abrir.\n\nPresiona el botón cuando estén afuera:", reply_markup=InlineKeyboardMarkup(keyboard))

async def job_1700_horno_critico(bot: Bot):
    if IS_PAUSED_TODAY:
        await send_telegram_alert(bot, "🌧️ **Día en Pausa:** Alerta de encender horno omitida por el Modo Emergencia/Lluvia.")
        return
    keyboard = [
        [InlineKeyboardButton("🔥 HORNO ENCENDIDO", callback_data="confirm_horno")]
    ]
    await send_telegram_alert(bot, "🔥 **05:00 PM - ¡ALERTA CRÍTICA PIZZERÍA!**\n\n⚠️ **ENCENDER EL HORNO AHORA** para el precalentamiento a 06:00 PM.\n\nPresiona el botón cuando el horno esté encendido:", reply_markup=InlineKeyboardMarkup(keyboard))

async def job_1800_pizzeria(bot: Bot):
    if IS_PAUSED_TODAY:
        await send_telegram_alert(bot, "🌧️ **Pizzería en Pausa Hoy:** Disfruta de tu descanso o tiempo de mantenimiento.")
        return
    await send_telegram_alert(bot, "🍕 **06:00 PM - APERTURA DE LA PIZZERÍA**\n\n¡Éxito en las ventas de hoy! Recuerda realizar tu 2ª comida Keto durante la jornada.")

async def job_2230_formulario(bot: Bot):
    webapp_url = config.WEBAPP_URL
    keyboard = [
        [InlineKeyboardButton("📋 Abrir Formulario de Producción", url=f"{webapp_url}/app")]
    ]
    await send_telegram_alert(bot, "📋 **10:30 PM - Formulario de Producción de Mañana**\n\nIngresa los panes y pizzas a preparar mañana para calcular insumos y la lista de compras:", reply_markup=InlineKeyboardMarkup(keyboard))

async def job_2300_cierre(bot: Bot):
    # Desactivar pausa al finalizar el día
    set_paused_status(False)
    await send_telegram_alert(bot, "😴 **11:00 PM - Cierre de Jornada**\n\n¡Excelente trabajo hoy! Que tengas un descanso reparador. Mañana nos vemos a las 5:30 AM.")

async def job_sunday_report(bot: Bot):
    """Genera y envía el reporte semanal de rendimiento todos los domingos a las 8:00 PM."""
    db = SessionLocal()
    try:
        today = datetime.date.today()
        seven_days_ago = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        pomos = db.query(PomodoroLog).filter(PomodoroLog.date >= seven_days_ago).all()
        total_pomos = sum(p.cycles_completed for p in pomos)
        hours_studied = round((total_pomos * 25) / 60, 1)
        
        productions = db.query(DailyProduction).filter(DailyProduction.date >= seven_days_ago).all()
        total_pizzas = sum(p.quantity_planned for p in productions if "pizza" in p.product_name.lower())
        total_breads = sum(p.quantity_planned for p in productions if "pizza" not in p.product_name.lower())

        report = (
            "📊 **REPORTE SEMANAL DE RENDIMIENTO (Alexander Román)** 🏆\n\n"
            f"🍅 **Enfoque & Pomodoros:** {total_pomos} ciclos ({hours_studied} horas de estudio puro)\n"
            f"🏋️ **Salud & Ejercicio:** 7/7 días cumplidos\n"
            f"🐶 **Mascota:** Paseos semanales al día\n"
            f"🍕 **Producción Pizzería:** {total_pizzas} pizzas planificadas\n"
            f"🥖 **Producción Panadería:** {total_breads} panes horneados\n\n"
            "🔥 *¡Excelente trabajo esta semana! Mañana arrancamos con todo.* 💪"
        )
        await send_telegram_alert(bot, report)
    finally:
        db.close()

CURRENT_SHIFT_HOURS = 0.0

JOBS_MAP = [
    ("job_0530", job_0530_ejercicio, 5, 30, "🏋️ Ejercicio físico"),
    ("job_0630", job_0630_paseo_perro, 6, 30, "🐶 Paseo del Perro"),
    ("job_0730", job_0730_capcut, 7, 30, "🎬 CapCut / Edición (Pomodoro)"),
    ("job_0930", job_0930_panaderia, 9, 30, "🥖 Producción Panadería"),
    ("job_1130", job_1130_receta_keto, 11, 30, "🥗 Sugerencia Almuerzo Keto"),
    ("job_1330", job_1330_negocios, 13, 30, "💼 Negocios / Emprendimiento (Pomodoro)"),
    ("job_1500", job_1500_duolingo, 15, 0, "🦉 Duolingo / Idiomas"),
    ("job_1600", job_1600_masas_critico, 16, 0, "🚨 Alerta: Sacar masas de la refrigeradora"),
    ("job_1700", job_1700_horno_critico, 17, 0, "🔥 Alerta: Encender horno pizzería"),
    ("job_1800", job_1800_pizzeria, 18, 0, "🍕 Apertura Pizzería & 2ª Comida Keto"),
    ("job_2230", job_2230_formulario, 22, 30, "📋 Formulario Producción de Mañana"),
    ("job_2300", job_2300_cierre, 23, 0, "😴 Cierre de Jornada")
]

def shift_schedule_today(hours_shift: float, bot: Bot = None) -> str:
    """Desplaza todas las alertas del día por el número de horas indicado (ej: +1.0 o -0.5)."""
    global CURRENT_SHIFT_HOURS
    CURRENT_SHIFT_HOURS += hours_shift

    for job_id, func, orig_h, orig_m, title in JOBS_MAP:
        total_orig_minutes = orig_h * 60 + orig_m
        new_total_minutes = int(total_orig_minutes + CURRENT_SHIFT_HOURS * 60)
        new_total_minutes = max(0, min(1439, new_total_minutes))
        new_h = new_total_minutes // 60
        new_m = new_total_minutes % 60

        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        if bot:
            scheduler.add_job(
                func, 'cron',
                id=job_id,
                hour=new_h,
                minute=new_m,
                args=[bot],
                replace_existing=True
            )

    return get_current_schedule_summary()

def reset_schedule_today(bot: Bot = None) -> str:
    """Restablece los horarios originales del día."""
    global CURRENT_SHIFT_HOURS
    CURRENT_SHIFT_HOURS = 0.0
    return shift_schedule_today(0, bot)

def get_current_schedule_summary() -> str:
    """Devuelve la lista formateada de los horarios del día (aplicando el desplazamiento activo)."""
    summary = f"📅 **Agenda del Día**"
    if CURRENT_SHIFT_HOURS != 0:
        sign = "+" if CURRENT_SHIFT_HOURS > 0 else ""
        summary += f" *(Modificado: {sign}{CURRENT_SHIFT_HOURS:.1f}h)*"
    summary += ":\n\n"

    for job_id, func, orig_h, orig_m, title in JOBS_MAP:
        total_orig_minutes = orig_h * 60 + orig_m
        new_total_minutes = int(total_orig_minutes + CURRENT_SHIFT_HOURS * 60)
        new_total_minutes = max(0, min(1439, new_total_minutes))
        new_h = new_total_minutes // 60
        new_m = new_total_minutes % 60
        
        time_str = f"{new_h:02d}:{new_m:02d}"
        summary += f"• **{time_str}**: {title}\n"
    
    return summary

def setup_scheduler(bot: Bot):
    """
    Registra todos los cron jobs permanentes.
    IMPORTANTE: Los jobs con 'cron' se repiten TODOS los dias del anio automaticamente.
    No hay limite de fecha ni de mes. APScheduler los ejecuta indefinidamente.
    """
    # Detener scheduler si ya corria (evita jobs duplicados en reinicios de Render)
    if scheduler.running:
        try:
            scheduler.remove_all_jobs()
            print("[SCHEDULER]: Jobs anteriores eliminados para reinicio limpio.")
        except Exception as e:
            print(f"[SCHEDULER WARN]: {e}")
    
    registered = 0
    for job_id, func, orig_h, orig_m, title in JOBS_MAP:
        total_orig_minutes = orig_h * 60 + orig_m
        new_total_minutes = int(total_orig_minutes + CURRENT_SHIFT_HOURS * 60)
        new_total_minutes = max(0, min(1439, new_total_minutes))
        new_h = new_total_minutes // 60
        new_m = new_total_minutes % 60
        
        try:
            scheduler.add_job(
                func, 'cron',
                id=job_id,
                hour=new_h,
                minute=new_m,
                args=[bot],
                replace_existing=True,
                misfire_grace_time=300  # Si el servidor estuvo caido, ejecuta la tarea hasta 5 min tarde
            )
            registered += 1
        except Exception as e:
            print(f"[SCHEDULER ERROR] Job {job_id}: {e}")
    
    # Reporte Semanal: Domingos a las 8:00 PM (20:00) - todos los domingos del anio
    try:
        scheduler.add_job(
            job_sunday_report, 'cron',
            id='job_sunday_report',
            day_of_week='sun',
            hour=20, minute=0,
            args=[bot],
            replace_existing=True,
            misfire_grace_time=300
        )
        registered += 1
    except Exception as e:
        print(f"[SCHEDULER ERROR] job_sunday_report: {e}")

    # Auto-Ping Keep-Alive interno cada 9 minutos (complementa el de cron-job.org)
    try:
        scheduler.add_job(
            job_keep_alive, 'interval',
            minutes=9,
            id='job_keep_alive',
            args=[bot],
            replace_existing=True
        )
    except Exception as e:
        print(f"[SCHEDULER ERROR] job_keep_alive: {e}")

    if not scheduler.running:
        scheduler.start()
    
    print(f"[SCHEDULER]: {registered} alertas registradas exitosamente para todos los dias del anio.")
    print(f"[SCHEDULER]: Zona horaria: America/Caracas (VET UTC-4)")

