from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.settings import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Generador de sesiones de base de datos para dependencias de FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Crear todas las tablas definidas en los modelos al iniciar la aplicación
Base.metadata.create_all(engine)
