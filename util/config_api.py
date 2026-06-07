import threading
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.responses import FileResponse
import yaml
import os

log = logging.getLogger()


class WebConfigServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8081):
        self.host = host
        self.port = port
        self.app = FastAPI()
        self._server = None
        self._thread = None
        self._setup_routes()

    def _setup_routes(self):
        @self.app.post("/test")
        async def test_endpoint(payload: dict):
            return {"status": "ok", "received": payload}

        @self.app.get("/test")
        async def test_get():
            return {"status": "ok", "body": "it works"}

        @self.app.post("/coords")
        async def process_coords(payload: dict[str, int]):
            return {
                "message": "JSON успешно преобразован в Python dict",
                "data": payload,
                "types": {k: type(v).__name__ for k, v in payload.items()},
            }

        @self.app.get("/")
        async def get_site():
            return FileResponse("index.html")

        @self.app.get("/script.js")
        async def get_script():
            return FileResponse("script.js")

        @self.app.get("/drawing.js")
        async def get_drawing():
            return FileResponse("drawing.js")

    def start(self):
        """Запускает сервер в отдельном потоке"""
        if self._thread and self._thread.is_alive():
            print("⚠️ Сервер уже запущен")
            return
        log.info("Запуск http сервера")

        # Конфигурация и экземпляр сервера
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="warning"
        )
        self._server = uvicorn.Server(config)

        def _run():
            self._server.run()  # Блокирующий вызов, живёт в своём event loop

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        log.info(f"✅ FastAPI сервер запущен на http://{self.host}:{self.port}")

    def stop(self):
        """Корректно останавливает сервер"""
        if self._server and self._thread and self._thread.is_alive():
            self._server.should_exit = True  # Асинхронный сигнал к завершению
            self._thread.join(timeout=5)
            print("🛑 Сервер остановлен")
        else:
            print("⚠️ Сервер не запущен")


def load_yaml_config(path="config.yml"):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Файл '{path}' не найден.")

    with open(path, "r", encoding="utf-8") as f:
        try:
            # safe_load безопаснее, чем load, так как не исполняет произвольный Python-код
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Ошибка при парсинге YAML-файла: {e}")

    return data


def write_yaml_config(data, path="config.yml"):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Файл '{path}' не найден.")

    with open(path, "w", encoding="utf-8") as f:
        try:
            # safe_load безопаснее, чем load, так как не исполняет произвольный Python-код
            yaml.safe_dump(data, f)
        except yaml.YAMLError as e:
            raise ValueError(f"Ошибка при записи YAML-файла: {e}")
