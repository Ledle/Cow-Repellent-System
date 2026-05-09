import threading
import uvicorn
from fastapi import FastAPI


class ServerConfig:
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
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
                "types": {k: type(v).__name__ for k, v in payload.items()}
            }

    def start(self):
        """Запускает сервер в отдельном потоке"""
        if self._thread and self._thread.is_alive():
            print("⚠️ Сервер уже запущен")
            return

        # Конфигурация и экземпляр сервера
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)

        def _run():
            self._server.run()  # Блокирующий вызов, живёт в своём event loop

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        """Корректно останавливает сервер"""
        if self._server and self._thread and self._thread.is_alive():
            self._server.should_exit = True  # Асинхронный сигнал к завершению
            self._thread.join(timeout=5)
            print("🛑 Сервер остановлен")
        else:
            print("⚠️ Сервер не запущен")
