import os

class Config:
    APP_DB_USER = os.getenv("APP_DB_USER", "postgres")
    APP_DB_PASSWORD = os.getenv("APP_DB_PASSWORD", "postgres")
    DB_HOST = os.getenv("DB_HOST", "postgres")
    APP_DB_NAME = os.getenv("APP_DB_NAME", "cookbook")

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{APP_DB_USER}:{APP_DB_PASSWORD}@{DB_HOST}:5432/{APP_DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    KEYCLOAK_ISSUER_URL = os.getenv("KEYCLOAK_ISSUER_URL")