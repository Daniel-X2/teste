from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL

# Pool pequeno de propósito: o pooler do Supabase limita conexões simultâneas.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=2,
    max_overflow=3,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """Dependência do FastAPI: abre e fecha a sessão a cada requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
