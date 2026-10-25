import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from database.db import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_time = Column(String(50), nullable=True)  # Ej: "05:30", "16:00"
    category = Column(String(50), default="general")      # exercise, dog_walk, pizzeria, learning, general
    is_completed = Column(Boolean, default=False)
    priority = Column(String(20), default="normal")       # critical, high, normal
    repeat_daily = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PomodoroLog(Base):
    __tablename__ = "pomodoro_logs"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(100), nullable=False)           # CapCut, Business, Duolingo
    cycles_completed = Column(Integer, default=1)
    duration_minutes = Column(Integer, default=25)
    date = Column(String(10), nullable=False)             # YYYY-MM-DD
    notes = Column(Text, nullable=True)

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True) # Harina, Levadura, Queso, etc.
    quantity = Column(Float, default=0.0)
    unit = Column(String(20), default="kg")                 # kg, g, l, unidades
    min_threshold = Column(Float, default=5.0)

class DailyProduction(Base):
    __tablename__ = "daily_productions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), nullable=False)             # YYYY-MM-DD para el día de producción
    product_name = Column(String(100), nullable=False)   # Pizza Familiar, Baguette, etc.
    quantity_planned = Column(Integer, default=0)
    quantity_sold = Column(Integer, default=0)
    quantity_leftover = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class LearningLog(Base):
    __tablename__ = "learning_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), nullable=False)             # YYYY-MM-DD
    category = Column(String(50), nullable=False)         # CapCut, Business, Duolingo
    key_takeaway = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class KetoRecipe(Base):
    __tablename__ = "keto_recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    ingredients = Column(Text, nullable=False)
    instructions = Column(Text, nullable=False)
    net_carbs_g = Column(Float, default=5.0)
    protein_g = Column(Float, default=30.0)
    fat_g = Column(Float, default=40.0)
    prep_time_minutes = Column(Integer, default=15)
