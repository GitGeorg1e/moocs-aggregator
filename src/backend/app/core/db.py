from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from .config import settings

# MySQL (PyMySQL) — force utf8mb4 end-to-end
DATABASE_URL = (
    f"mysql+pymysql://{settings.db_user}:"
    f"{settings.db_password}@{settings.db_host}:"
    f"{settings.db_port}/{settings.db_name}"
    f"?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

@event.listens_for(engine, "connect")
def set_utf8mb4(dbapi_connection, connection_record):
    """Ensure every pooled connection uses utf8mb4 at the session level."""
    cursor = dbapi_connection.cursor()
    cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db():
    """Dependency για database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()