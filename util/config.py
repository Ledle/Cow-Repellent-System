import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource

default_config = {
    "model": {"name": "yolo26m", "fuse": True},
    "application": {
        "enable-web-ui": False,
        "enable-config-api": False,
        "logging-level": "info",
        "name": "Cow Reppelent System"
    },
}


class ModelConfig(BaseModel):
    name: str = default_config["model"]["name"]
    fuse: bool = default_config["model"]["fuse"]
    test: bool = False
    test_delay: int = Field(alias="test-delay", default=1)
    verbose: bool = False


class ApplicationConfig(BaseModel):
    enable_web_ui: bool = Field(
        alias="enable-web-ui", default=default_config["application"]["enable-web-ui"]
    )
    enable_config_api: bool = Field(
        alias="enable-config-api",
        default=default_config["application"]["enable-config-api"],
    )
    logging_level: str = Field(
        alias="logging-level", default=default_config["application"]["logging-level"]
    )

    model_config = SettingsConfigDict(populate_by_name=True)
    name: str = Field(default=default_config["application"]["name"])


class RepellerConfig(BaseModel):
    name: str
    type: str = "test"
    camera: str = ""
    url: str = ""
    enabled: bool = False


class CameraConfig(BaseModel):
    name: str
    url: str
    enable: bool = True
    track: bool = True
    test: bool = False


class Settings(BaseSettings):
    """
    Корневая конфигурация приложения.
    Автоматически загружает данные из config.toml
    """

    model: ModelConfig
    application: ApplicationConfig
    repeller: Optional[List[RepellerConfig]] = Field(default_factory=list)
    camera: Optional[List[CameraConfig]] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        extra="forbid",  # Запретить неизвестные поля в TOML
        populate_by_name=True,  # Принимать как alias, так и имена полей
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        toml_path = os.getenv("CONFIG_FILE", "config.toml")
        """
        Настраиваем приоритет источников:
        1. Явные аргументы конструктора
        2. TOML-файл
        3. Переменные окружения
        4. .env файл
        """
        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls, Path(toml_path)),
            env_settings,
            dotenv_settings,
        )
