from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import settings

connector = Connector()


def _get_connection():
    return connector.connect(
        settings.cloud_sql_instance.strip(),
        "pymysql",
        user=settings.db_user.strip(),
        password=settings.db_password.strip(),
        db=settings.db_name.strip(),
    )


engine = create_engine("mysql+pymysql://", creator=_get_connection, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
