import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-centro-salud-2026")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-centro-salud-periurbano-2026")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "15"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))
    )
    
    # Horas hábiles del centro de salud periurbano (consistente con el frontend)
    HORAS_JORNADA = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    
    # Supabase / PostgreSQL opcionales
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Rate Limiting por defecto
    RATELIMIT_DEFAULT = "60 per minute"
    RATELIMIT_STORAGE_URI = "memory://"
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    RATELIMIT_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
