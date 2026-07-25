from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import settings

if settings.db_host:
    # Local dev: direct MySQL connection, no Cloud SQL Connector needed
    _url = (
        f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}/{settings.db_name}"
    )
    engine = create_engine(_url, pool_pre_ping=True)
else:
    # Production: Cloud SQL Connector (IAM auth via service account)
    from google.cloud.sql.connector import Connector

    _connector = Connector()

    def _get_connection():
        return _connector.connect(
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
