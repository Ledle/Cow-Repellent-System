import asyncio
import threading
import queue
import json
import websockets
import logging

log = logging.getLogger()


class SyncWSServer:
    """WebSocket-сервер, который работает из синхронного потока."""

    def __init__(self, host="0.0.0.0", port=8080, buffer_size=5):
        self.host = host
        self.port = port
        self.queue = queue.Queue(maxsize=buffer_size)
        self._loop = None
        self._thread = None
        self._ready = threading.Event()

    def _run_async_server(self):
        async def handler(websocket):
            print(f"👤 Клиент подключён: {websocket.remote_address}")
            try:
                while True:
                    # Ждём данные из очереди. Таймаут нужен, чтобы сервер
                    # мог корректно реагировать на закрытие соединения.
                    try:
                        img_bytes, boxes = self.queue.get(timeout=1.0)
                    except queue.Empty:
                        continue

                    # 1. Кадр уходит как binary frame
                    await websocket.send(img_bytes)
                    # 2. JSON уходит как text frame
                    await websocket.send(json.dumps({"boxes": boxes}))

            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                print("🔌 Клиент отключён")

        async def main():
            # Запускаем сервер
            async with websockets.serve(handler, self.host, self.port):
                self._ready.set()  # Сигнал: сокет открыт и готов принимать подключения
                print(f"🚀 WS Server запущен на ws://{self.host}:{self.port}")
                await asyncio.Future()  # Вечное ожидание

        # Создаём и запускаем event loop в отдельном потоке
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(main())

    def start(self):
        """Запускает сервер в фоновом потоке."""
        log.info("Запуск сокета")
        self._thread = threading.Thread(target=self._run_async_server, daemon=True)
        self._thread.start()
        self._ready.wait()  # Блокируем вызов start(), пока сокет реально не откроется

    def send(self, image_bytes: bytes, boxes: list):
        """Отправляет кадр и рамки. Не блокирует основной поток."""
        # Если очередь переполнена, дропаем самый старый кадр, чтобы не тормозить цикл
        if self.queue.full():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass
        self.queue.put_nowait((image_bytes, boxes))

    def stop(self):
        """Корректно останавливает сервер."""
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
