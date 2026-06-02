from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    cloud_sql_instance: str  # project:region:instance
    db_name: str
    db_user: str
    db_password: str
    app_env: str = "production"


settings = Settings()
