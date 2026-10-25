import asyncio
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import config
from database.db import SessionLocal
from database.models import PomodoroLog, Task, InventoryItem, DailyProduction, LearningLog
from services.keto_chef import keto_chef
from services.inventory_service import inventory_service
from services.gemini_service import gemini_service

async def safe_reply(update: Update, text: str, reply_markup=None):
    """Envía un mensaje de forma segura intentando Markdown y con fallback a texto plano."""
    try:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception as e:
        print(f"[SAFELY FALLING BACK TO PLAIN TEXT]: {e}")
        try:
            await update.message.reply_text(text, reply_markup=reply_markup)
        except Exception as ex:
            print(f"[FAILED TO SEND TELEGRAM MESSAGE]: {ex}")

async def safe_edit(query, text: str, reply_markup=None):
    """Edita un mensaje de forma segura intentando Markdown y con fallback a texto plano."""
    try:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception as e:
        print(f"[SAFELY FALLING BACK TO PLAIN TEXT EDIT]: {e}")
        try:
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as ex:
            print(f"[FAILED TO EDIT TELEGRAM MESSAGE]: {ex}")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guarda el Chat ID y muestra el menú principal interactivo."""
    chat_id = str(update.effective_chat.id)
    config.TELEGRAM_CHAT_ID = chat_id
    
    welcome_text = (
        "🤖 **¡Hola Alexander! Soy tu Super Asistente Personal y de Negocio**\n\n"
        "Estoy configurado para acompañarte en tu rutina diaria, tu dieta Keto, el paseo de tu mascota, "
        "tus bloques de aprendizaje con el **Método Pomodoro** y la operación de tu **Pizzería y Panadería**.\n\n"
        "📍 **Comandos Disponibles:**\n"
        "• `/status` - Resumen del día y metas\n"
        "• `/pomodoro` - Iniciar temporizador de enfoque (25m)\n"
        "• `/keto` - Sugerencia de almuerzo Keto\n"
        "• `/inventario` - Consultar insumos de pizzería\n"
        "• `/produccion` - Registrar producción de mañana\n"
        "• `/pausar` - Pausar alertas de la pizzería hoy (Modo Lluvia/Emergencia)\n"
        "• `/reportesemanal` - Ver reporte de rendimiento semanal\n\n"
        "🎙️ *¡Puedes escribirme cualquier pregunta o enviarme notas de voz en cualquier momento!*"
    )
    keyboard = [
        [InlineKeyboardButton("🍅 Iniciar Pomodoro", callback_data="start_pomo_menu"), InlineKeyboardButton("🥗 Receta Keto", callback_data="keto_refresh")],
        [InlineKeyboardButton("🐶 Paseo del Perro (30m)", callback_data="start_dog_walk"), InlineKeyboardButton("📋 Producción", callback_data="open_production")],
        [InlineKeyboardButton("🌧️ Pausar Jornada (Emergencia)", callback_data="pause_today")]
    ]
    await safe_reply(update, welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el estado del día y Pomodoros acumulados."""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    db = SessionLocal()
    try:
        pomos = db.query(PomodoroLog).filter(PomodoroLog.date == today_str).all()
        total_pomos = sum(p.cycles_completed for p in pomos)
        
        status_text = (
            f"📊 **Resumen del Día ({today_str})**\n\n"
            f"🍅 **Pomodoros completados hoy:** {total_pomos} ({total_pomos * 25} minutos de estudio puro)\n"
            f"🏋️ **Ejercicio (5:30 AM):** ✅ Programado\n"
            f"🐶 **Paseo Mascota (6:30 AM):** ✅ Programado\n"
            f"🥖 **Producción Panadería:** ✅ 4 horas programadas\n"
            f"🍕 **Estado Pizzería:** Listos para abrir a las 6:00 PM"
        )
        await safe_reply(update, status_text)
    finally:
        db.close()

async def cmd_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el inventario actual de materia prima."""
    db = SessionLocal()
    try:
        items = db.query(InventoryItem).all()
        if not items:
            default_items = [
                InventoryItem(name="Harina", quantity=25.0, unit="kg"),
                InventoryItem(name="Levadura", quantity=1.0, unit="kg"),
                InventoryItem(name="Queso Mozzarella", quantity=10.0, unit="kg"),
                InventoryItem(name="Salsa de Tomate", quantity=8.0, unit="kg"),
                InventoryItem(name="Agua", quantity=50.0, unit="L")
            ]
            db.add_all(default_items)
            db.commit()
            items = db.query(InventoryItem).all()

        text = "📦 **Inventario Actual de Insumos (Pizzería/Panadería):**\n\n"
        for item in items:
            status_icon = "🟢" if item.quantity > item.min_threshold else "🔴"
            text += f"{status_icon} **{item.name}:** {item.quantity} {item.unit}\n"
            
        await safe_reply(update, text)
    finally:
        db.close()

async def cmd_keto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía una receta Keto rápida."""
    recipe = await keto_chef.get_daily_recipe()
    keyboard = [[InlineKeyboardButton("🔄 Probar Otra Receta", callback_data="keto_refresh")]]
    await safe_reply(update, f"🥗 **Receta Keto del Día:**\n\n{recipe}", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa los clics en botones interactivos."""
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = query.message.chat_id

    if data == "start_dog_walk":
        await safe_edit(query, 
            "🐶 **¡Paseo del Perro Iniciado! (30 Minutos)**\n\n"
            "Disfruta la caminata con tu mascota. Te enviaré una alerta a los 25 minutos para regresar a casa. ⏳"
        )
        await asyncio.sleep(25 * 60) # 25 minutos
        await context.bot.send_message(chat_id=chat_id, text="⌛ **¡Quedan 5 minutos de paseo!** Es hora de regresar a casa para tu ducha de las 7:00 AM. 🚿")

    elif data == "snooze_dog_walk":
        await safe_edit(query, "⏰ **Paseo reprogramado para las 03:30 PM.** ¡Agenda ajustada!")

    elif data in ["pomo_capcut_1", "pomo_business_1", "start_pomo_menu"]:
        topic = "CapCut" if "capcut" in data else ("Negocios" if "business" in data else "Enfoque")
        await safe_edit(query, 
            f"🍅 **Pomodoro Iniciado: {topic} (25 Minutos)**\n\n"
            "Cierra distracciones y enfócate. Te avisaré cuando sea tiempo de descansar. 🧠🔥"
        )
        await asyncio.sleep(25 * 60)
        
        db = SessionLocal()
        try:
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            pomo_entry = PomodoroLog(topic=topic, cycles_completed=1, duration_minutes=25, date=today_str)
            db.add(pomo_entry)
            db.commit()
        finally:
            db.close()

        keyboard = [[InlineKeyboardButton("▶️ Iniciar Siguiente Pomodoro", callback_data="start_pomo_menu")]]
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔔 **¡TIEMPO! Pomodoro de {topic} Completado (25m)** 🎉\n\n"
                 "Tómate 5 minutos de descanso. Estira las piernas y toma agua. ☕",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "confirm_masas":
        await safe_edit(query, "✅ **¡CONFIRMADO! Masas fuera de la refrigeradora a las 04:00 PM.** ¡Proceso registrado correctamente!")

    elif data == "confirm_horno":
        await safe_edit(query, "🔥 **¡CONFIRMADO! Horno encendido a las 05:00 PM.** ¡Temperatura alcanzada para abrir a las 6:00 PM!")

    elif data == "pause_today":
        from scheduler.cron_jobs import set_paused_status
        set_paused_status(True)
        await safe_edit(query, "🌧️ **Modo Emergencia / Día Lluvioso Activado:** Las alertas de sacar masas (4PM) y encender horno (5PM) han sido pausadas por hoy.")

    elif data == "keto_refresh":
        recipe = await keto_chef.get_daily_recipe()
        keyboard = [[InlineKeyboardButton("🔄 Probar Otra Receta", callback_data="keto_refresh")]]
        await safe_edit(query, f"🥗 **Nueva Sugerencia Keto:**\n\n{recipe}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "reset_schedule":
        from scheduler.cron_jobs import reset_schedule_today
        new_sched = reset_schedule_today(context.bot)
        await safe_edit(query, f"🔄 **Horario restablecido a su agenda original:**\n\n{new_sched}")

async def cmd_pausar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activa o desactiva el Modo Emergencia / Día Lluvioso."""
    from scheduler.cron_jobs import set_paused_status, IS_PAUSED_TODAY
    new_status = not IS_PAUSED_TODAY
    set_paused_status(new_status)
    status_text = "🌧️ **MODO EMERGENCIA/LLUVIA ACTIVADO:** Alertas de pizzería pausadas hoy." if new_status else "☀️ **MODO DÍA NORMAL ACTIVADO:** Alertas de pizzería restablecidas."
    await safe_reply(update, status_text)

async def cmd_posponer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite posponer o rodar el horario del día (ej: /posponer 1h, /posponer 30m, /posponer reset)."""
    from scheduler.cron_jobs import shift_schedule_today, reset_schedule_today
    
    args = context.args
    if not args:
        help_txt = (
            "⏰ **Ajuste de Horario Dinámico**\n\n"
            "Puedes desplazar todas las alertas del día con estos comandos:\n"
            "• `/posponer 1h` - Posponer agenda 1 hora\n"
            "• `/posponer 30m` - Posponer agenda 30 minutos\n"
            "• `/posponer -1h` - Adelantar agenda 1 hora\n"
            "• `/posponer reset` - Volver al horario normal\n\n"
            "*¡También puedes decírselo a tu asistente por nota de voz o mensaje libre!*"
        )
        await safe_reply(update, help_txt)
        return

    param = args[0].lower()
    if param in ["reset", "restablecer", "0"]:
        new_sched = reset_schedule_today(context.bot)
        await safe_reply(update, f"🔄 **Horario restablecido a su agenda original:**\n\n{new_sched}")
        return

    hours = 0.0
    if param.endswith("h"):
        try:
            hours = float(param.replace("h", ""))
        except ValueError:
            hours = 1.0
    elif param.endswith("m"):
        try:
            hours = float(param.replace("m", "")) / 60.0
        except ValueError:
            hours = 0.5
    else:
        try:
            hours = float(param)
        except ValueError:
            hours = 1.0

    new_sched = shift_schedule_today(hours, context.bot)
    sign = "+" if hours > 0 else ""
    keyboard = [[InlineKeyboardButton("🔄 Restablecer horario original", callback_data="reset_schedule")]]
    await safe_reply(
        update,
        f"✅ **¡Horario desplazado {sign}{hours:.1f} horas exitosamente!**\n\n"
        f"Las alertas automáticas del día han sido re-programadas a las nuevas horas:\n\n{new_sched}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cmd_reportesemanal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el reporte semanal de rendimiento."""
    from scheduler.cron_jobs import job_sunday_report
    await job_sunday_report(context.bot)


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa mensajes de voz recibidos en Telegram (Hands-Free) usando la IA Multimodal de Gemini."""
    chat_id = str(update.effective_chat.id)
    config.TELEGRAM_CHAT_ID = chat_id

    # Notificar que se está escuchando el audio
    msg = await update.message.reply_text("🎙️ **Escuchando tu nota de voz con IA...** 🧠")

    try:
        # Descargar el archivo de audio OGG de Telegram
        file_info = await context.bot.get_file(update.message.voice.file_id)
        voice_bytes = await file_info.download_as_bytearray()

        prompt = f"""
Escucha atentamente el audio adjunto enviado por Alexander Román a su asistente virtual.
Esta es la agenda oficial completa de Alexander:
- 05:30 AM: Ejercicio físico (1 hora).
- 06:30 AM: Paseo del Perro (20-30 min).
- 07:00 AM: Ducha e Higiene personal.
- 07:30 AM: Bloque 1 de Aprendizaje (CapCut / Edición con Método Pomodoro - 2 horas).
- 09:30 AM: Producción de Panadería (4 horas).
- 11:30 AM: Sugerencia de Almuerzo Keto (<20g carbohidratos netos).
- 12:00 PM: 1ª Comida del Día (Almuerzo Keto).
- 01:30 PM: Bloque 2 de Aprendizaje (Negocios y Emprendimiento con Pomodoro - 1.5 horas).
- 03:00 PM: Duolingo / Lección de Idiomas (30 min).
- 03:30 PM: Descanso Largo / Tiempo Libre (30 min).
- 04:00 PM: ALERTA CRÍTICA: Sacar masas de la refrigeradora.
- 05:00 PM: ALERTA CRÍTICA: Encender el horno de la pizzería.
- 06:00 PM - 11:00 PM: Apertura de la Pizzería y 2ª Comida Keto.
- 10:30 PM: Formulario de Producción de Mañana y Lista de Compras.
- 11:00 PM: Cierre de Caja y Descanso Nocturno.

Instrucciones:
1. Transcribe lo que Alexander dice en el audio.
2. Responde directamente a lo que Alexander pide o pregunta en el audio con su contexto personal y de negocio.
3. Si pide su agenda, muéstrasela COMPLETA desde las 05:30 AM comenzando con el Ejercicio.
        """

        ai_response = await gemini_service.generate_from_audio(bytes(voice_bytes), prompt)

        if not ai_response:
            ai_response = "🤖 **Asistente:** Escuché tu nota de voz. Estoy aquí para mantener al día tu agenda, la pizzería y tus bloques de estudio."

        try:
            await msg.edit_text(ai_response, parse_mode="Markdown")
        except Exception:
            await msg.edit_text(ai_response)

    except Exception as e:
        print(f"Error procesando nota de voz: {e}")
        await msg.edit_text("🤖 **Asistente:** Recibí tu audio. ¿Deseas consultar tu agenda o agregar un recordatorio?")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa cualquier mensaje de texto libre mediante la Inteligencia Artificial de Gemini."""
    user_text = update.message.text
    chat_id = str(update.effective_chat.id)
    config.TELEGRAM_CHAT_ID = chat_id

    lower_txt = user_text.lower()
    if any(w in lower_txt for w in ["pospon", "rodar", "correr", "desplazar", "atrasar", "mas tarde", "más tarde"]):
        from scheduler.cron_jobs import shift_schedule_today
        hours = 1.0
        if "30" in lower_txt or "media" in lower_txt:
            hours = 0.5
        elif "2" in lower_txt:
            hours = 2.0
        elif "3" in lower_txt:
            hours = 3.0
        new_sched = shift_schedule_today(hours, context.bot)
        keyboard = [[InlineKeyboardButton("🔄 Restablecer horario original", callback_data="reset_schedule")]]
        await safe_reply(
            update,
            f"✅ **¡Horario re-programado +{hours:.1f}h exitosamente!**\n\n"
            f"Todas tus alertas automáticas de hoy se han corrido {hours:.1f} hora(s):\n\n{new_sched}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    prompt = f"""
Eres el Super Asistente Personal y de Negocio de Alexander Román.
Esta es la agenda oficial completa de Alexander:
- 05:30 AM: Ejercicio físico (1 hora).
- 06:30 AM: Paseo del Perro (20-30 min).
- 07:00 AM: Ducha e Higiene personal.
- 07:30 AM: Bloque 1 de Aprendizaje (CapCut / Edición con Método Pomodoro - 2 horas).
- 09:30 AM: Producción de Panadería (4 horas).
- 11:30 AM: Sugerencia de Almuerzo Keto (<20g carbohidratos netos).
- 12:00 PM: 1ª Comida del Día (Almuerzo Keto).
- 01:30 PM: Bloque 2 de Aprendizaje (Negocios y Emprendimiento con Pomodoro - 1.5 horas).
- 03:00 PM: Duolingo / Lección de Idiomas (30 min).
- 03:30 PM: Descanso Largo / Tiempo Libre (30 min).
- 04:00 PM: ALERTA CRÍTICA: Sacar masas de la refrigeradora.
- 05:00 PM: ALERTA CRÍTICA: Encender el horno de la pizzería.
- 06:00 PM - 11:00 PM: Apertura de la Pizzería y 2ª Comida Keto.
- 10:30 PM: Formulario de Producción de Mañana y Lista de Compras.
- 11:00 PM: Cierre de Caja y Descanso Nocturno.

Mensaje de Alexander: "{user_text}"

Instrucciones de respuesta:
1. Si Alexander te pide su agenda o su rutina, muéstrale SIEMPRE la agenda COMPLETA desde las 05:30 AM comenzando con el Ejercicio.
2. Responde de forma amable, cercana, directa y estructurada en Markdown.
3. Si te hace cualquier otra pregunta (sobre pizza, recetas Keto, CapCut, o negocios), respóndele como un experto consejero personal.
    """
    
    ai_response = await gemini_service.generate_text(prompt)
    if not ai_response:
        lower_txt = user_text.lower()
        if any(w in lower_txt for w in ["agenda", "rutina", "hacer", "hago", "horario", "dia", "día", "tarea"]):
            ai_response = (
                "📅 **Tu Rutina y Agenda Oficial del Día:**\n\n"
                "• **05:30 AM**: 🏋️ Ejercicio físico (1 hora)\n"
                "• **06:30 AM**: 🐶 Paseo del Perro (20-30 min)\n"
                "• **07:00 AM**: 🚿 Ducha e Higiene personal\n"
                "• **07:30 AM**: 🎬 Bloque 1: CapCut / Edición (Pomodoro - 2h)\n"
                "• **09:30 AM**: 🥖 Producción Panadería (4h)\n"
                "• **11:30 AM**: 🥗 Almuerzo Keto (Sugerencia de receta)\n"
                "• **12:00 PM**: 🍽️ 1ª Comida (Almuerzo Keto)\n"
                "• **01:30 PM**: 💼 Bloque 2: Negocios y Emprendimiento (Pomodoro - 1.5h)\n"
                "• **03:00 PM**: 🦉 Duolingo / Idiomas (30 min)\n"
                "• **03:30 PM**: ☕ Descanso Largo (30 min)\n"
                "• **04:00 PM**: 🚨 ALERTA: Sacar masas de la refrigeradora\n"
                "• **05:00 PM**: 🔥 ALERTA: Encender horno pizzería\n"
                "• **06:00 PM**: 🍕 Apertura Pizzería & 2ª Comida Keto\n"
                "• **10:30 PM**: 📋 Formulario Producción de Mañana\n"
                "• **11:00 PM**: 😴 Cierre y Descanso\n"
            )
        else:
            ai_response = f"🤖 **Asistente Phenix Infinity:**\n\nProcesé tu consulta: *\"{user_text}\"*\n\n¿Deseas consultar tu agenda del día (`/status`), iniciar un temporizador (`/pomodoro`), o ver tu receta Keto (`/keto`)?"

    await safe_reply(update, ai_response)
