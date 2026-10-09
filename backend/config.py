

import os

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Settings:
    # Application settings
    APP_NAME: str = os.getenv(
        "APP_NAME",
        "SmartEvent API",
    )

    APP_VERSION: str = os.getenv(
        "APP_VERSION",
        "2.0.0",
    )

    DEBUG: bool = os.getenv(
        "DEBUG",
        "False",
    ).lower() == "true"

    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./smartevent.db",
    )

    # JWT authentication settings
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "",
    )

    ALGORITHM: str = os.getenv(
        "ALGORITHM",
        "HS256",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            "30",
        )
    )

    # Frontend CORS configuration
    FRONTEND_URL: str = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173",
    )

    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY is missing. Configure it in the .env file."
            )

        if cls.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
            raise RuntimeError(
                "ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero."
            )


settings = Settings()
