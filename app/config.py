from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    cloud_sql_instance: str = ""  # project:region:instance (not needed when db_host is set)
    db_name: str
    db_user: str
    db_password: str
    db_host: str = ""  # Local dev only; when set, bypasses Cloud SQL Connector
    app_env: str = "production"


settings = Settings()
