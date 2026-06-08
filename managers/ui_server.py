import asyncio
import base64
import io
import os
import json
import random
import time
import cv2
import toml
import numpy as np
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont
from .application_manager import ApplicationManager
from util.config import ModelConfig, ApplicationConfig


# === PYDANTIC МОДЕЛИ (Оставлены на уровне модуля для корректной работы FastAPI) ===


class DeviceCreate(BaseModel):
    name: str
    url: str
    enable: bool = True


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    enable: Optional[bool] = None
    active: Optional[bool] = None


class CameraCreate(BaseModel):
    name: str
    url: str
    test: bool = True
    resolution: str = "1920x1080"
    fps: int = 30


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    test: Optional[bool] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None


class Point(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)


class ZoneCreate(BaseModel):
    name: str
    points: List[Point] = Field(..., min_length=3)
    color: Optional[str] = "#00ff00"
    active: bool = True
    linked_devices: List[str] = []


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    points: Optional[List[Point]] = None
    color: Optional[str] = None
    active: Optional[bool] = None
    linked_devices: Optional[List[str]] = None


class SettingsUpdate(BaseModel):
    model: Optional[dict] = None
    application: Optional[dict] = None


# === КЛАСС СЕРВЕРА ===

PARENT_DIR: str = "front/"


class UIServer:
    def __init__(self, app_manager: ApplicationManager):
        self.app = FastAPI(title="VisionGuard UI Server")
        self.application_manager = app_manager
        # Инициализация состояния (вместо глобальных переменных)
        self.device_counter = 3
        self.camera_counter = 3

        self.CAMERAS = {
            "cam_01": {
                "name": "Камера 1 (Главный вход)",
                "url": "rtsp://example.com/cam1",
                "test": True,
                "resolution": "1920x1080",
                "fps": 30,
            },
            "cam_02": {
                "name": "Камера 2 (Складская зона)",
                "url": "rtsp://example.com/cam2",
                "test": True,
                "resolution": "1280x720",
                "fps": 25,
            },
        }

        self.DEVICES = {
            "dev_01": {
                "id": "dev_01",
                "name": "Отпугиватель 1",
                "url": "http://192.168.1.10/api/trigger",
                "enable": True,
            },
            "dev_02": {
                "id": "dev_02",
                "name": "Отпугиватель 2",
                "url": "http://192.168.1.11/api/trigger",
                "enable": True,
            },
        }

        self.ZONES = {"cam_01": [], "cam_02": []}
        self.ACTIVE_WEBSOCKETS = {}
        self.ACTIVE_DEVICE_WEBSOCKETS = set()

        # Настройка приложения
        self._setup_cors()
        self._setup_routes()
        self._load_fonts()

        self.application_manager.device_manager.on_change = self._on_device_change

    def _setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_site_routes(self, app):
        # --- HTML СТРАНИЦЫ ---
        @app.get("/", response_class=HTMLResponse)
        async def read_root():
            try:
                with open(PARENT_DIR + "index.html", "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                return "<h1>index.html не найден</h1>"

        @app.get("/devices", response_class=HTMLResponse)
        async def read_devices():
            try:
                with open(PARENT_DIR + "devices.html", "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                return "<h1>devices.html не найден</h1>"

        @app.get("/zones", response_class=HTMLResponse)
        async def read_zones():
            try:
                with open(PARENT_DIR + "zones.html", "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                return "<h1>zones.html не найден</h1>"

        @app.get("/settings", response_class=HTMLResponse)
        async def read_settings():
            try:
                with open(PARENT_DIR + "settings.html", "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                return "<h1>settings.html не найден</h1>"

    def _setup_device_routes(self, app):
        # --- REST API: УСТРОЙСТВА ---
        @app.get("/api/devices")
        async def get_devices():
            manager = self.application_manager.device_manager
            return manager.serialize_devices()

        @app.post("/api/devices")
        async def create_device(device: DeviceCreate):
            manager = self.application_manager.device_manager
            device = manager.make_device_from_dict(device.dict())
            return {"status": "created", "id": device.id}

        @app.put("/api/devices/{device_id}")
        async def update_device(device_id: str, device: DeviceUpdate):
            manager = self.application_manager.device_manager
            d = manager.get_device_by_id(device_id)
            if d is None:
                raise HTTPException(status_code=404, detail="Устройство не найдено")

            if device.name is not None:
                d.name = device.name
            if device.url is not None:
                d.url = device.url
            if device.active is not None:
                manager.switch_device(device.active)
            if device.enable is not None:
                manager.toggle_device(d, device.enable)

            return {"status": "updated", "id": d.id}

        @app.delete("/api/devices/{device_id}")
        async def delete_device(device_id: str):
            manager = self.application_manager.device_manager
            d = manager.get_device_by_id(device_id)
            if d is None:
                raise HTTPException(status_code=404, detail="Устройство не найдено")

            for zones in self.ZONES.values():
                for z in zones:
                    if device_id in z["linked_devices"]:
                        z["linked_devices"].remove(device_id)

            return {"status": "deleted", "id": device_id}

    def _setup_system_routes(self, app):
        @app.get("/api/system/status")
        async def get_system_status():
            manager = self.application_manager.video_source_manager
            camera_list = manager.serialize_sources()
            return {
                "name": self.application_manager.get_name(),
                "uptime": self.application_manager.get_uptime(),
                "status": self.application_manager.get_status(),
                "cameras": camera_list,
            }

    def _setup_settings_routes(self, app):
        @app.get("/api/settings")
        async def get_settings():
            config_path = os.getenv("CONFIG_FILE", "config.toml")
            try:
                config = toml.load(config_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка чтения конфига: {e}")
            return {
                "model": config.get("model", {}),
                "application": config.get("application", {}),
            }

        @app.put("/api/settings")
        async def update_settings(payload: SettingsUpdate):
            config_path = os.getenv("CONFIG_FILE", "config.toml")
            try:
                existing = toml.load(config_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка чтения конфига: {e}")

            if payload.model is not None:
                try:
                    validated = ModelConfig(**payload.model)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Ошибка модели: {e}")
                existing["model"] = validated.model_dump()

            if payload.application is not None:
                try:
                    validated = ApplicationConfig(**payload.application)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Ошибка конфигурации: {e}")
                existing["application"] = validated.model_dump()

            try:
                with open(config_path, "w", encoding="utf-8") as f:
                    toml.dump(existing, f)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка записи конфига: {e}")

            if payload.model is not None:
                existing["model"].pop("model_config", None)
                self.application_manager.detection_manager.set_model(None)
            if payload.application is not None:
                existing["application"].pop("model_config", None)

            return {"status": "ok", "model": existing.get("model"), "application": existing.get("application")}

    def _setup_source_routes(self, app):
        # --- REST API: КАМЕРЫ ---
        @app.get("/api/camera/{camera_id}")
        async def get_camera(camera_id: str):
            manager = self.application_manager.video_source_manager
            s = manager.get_source_by_id(camera_id)
            if s is None:
                raise HTTPException(status_code=404, detail="Камера не найдена")
            return manager.serialize_source(s)

        @app.get("/api/camera/{camera_id}/info")
        async def get_camera_info(camera_id: str):
            manager = self.application_manager.video_source_manager
            s = manager.get_source_by_id(camera_id)
            if s is None:
                raise HTTPException(status_code=404, detail="Камера не найдена")
            width, height = s.get_resolution()
            resolution = f"{str(width)}x{str(height)}"
            return {
                "socketUrl": f"ws://localhost:8000/ws/{s.id}",
                "resolution": resolution,
                "fps": s.get_fps(),
                "enabled": s.enabled,
            }

        @app.post("/api/camera")
        async def create_camera(camera: CameraCreate):
            manager = self.application_manager.video_source_manager

            cam_id = manager.create_source_from_dict(camera.dict())

            return {"status": "created", "id": cam_id}

        @app.put("/api/camera/{camera_id}")
        async def update_camera(camera_id: str, camera: CameraUpdate):
            manager = self.application_manager.video_source_manager
            s = manager.get_source_by_id(camera_id)
            if s is None:
                raise HTTPException(status_code=404, detail="Камера не найдена")

            cam_data = self.CAMERAS[camera_id]
            if camera.name is not None:
                cam_data["name"] = camera.name
            if camera.url is not None:
                cam_data["url"] = camera.url
            if camera.test is not None:
                cam_data["test"] = camera.test
            if camera.resolution is not None:
                pass  # TODO
            if camera.fps is not None:
                pass  # TODO

            return {"status": "updated", "id": camera_id}

        @app.delete("/api/camera/{camera_id}")
        async def delete_camera(camera_id: str):
            manager = self.application_manager.video_source_manager
            s = manager.get_source_by_id(camera_id)
            if s is None:
                raise HTTPException(status_code=404, detail="Камера не найдена")

            if camera_id in self.ACTIVE_WEBSOCKETS:
                try:
                    await self.ACTIVE_WEBSOCKETS[camera_id].close(
                        code=1000, reason="Camera deleted"
                    )
                except Exception:
                    pass
                del self.ACTIVE_WEBSOCKETS[camera_id]

            manager.remove_source(s)
            self.ZONES.pop(camera_id, None)

            return {"status": "deleted", "id": camera_id}

    def _setup_zone_routes(self, app):
        # --- REST API: ЗОНЫ ---
        @app.get("/api/camera/{camera_id}/zones")
        async def get_zones(camera_id: str):
            src_manager = self.application_manager.video_source_manager
            detection_manager = self.application_manager.detection_manager
            s = src_manager.get_source_by_id(camera_id)
            if s is None:
                raise HTTPException(status_code=404, detail="Камера не найдена")

            zones = detection_manager.get_source_zones(s)
            enriched_zones = []
            return detection_manager.serialize_zones(zones)

        @app.post("/api/camera/{camera_id}/zone")
        async def create_zone(camera_id: str, zone: ZoneCreate):
            src_manager = self.application_manager.video_source_manager
            s = src_manager.get_source_by_id(camera_id)
            dev_manager = self.application_manager.device_manager
            detect_manager = self.application_manager.detection_manager
            if s is None:
                raise HTTPException(status_code=404, detail="Камера не найдена")
            if len(zone.points) < 3:
                raise HTTPException(status_code=400, detail="Минимум 3 точки")

            for dev_id in zone.linked_devices:
                dev = dev_manager.get_device_by_id(dev_id)
                if dev is None:
                    raise HTTPException(
                        status_code=400, detail=f"Устройство {dev_id} не найдено"
                    )
            data = zone.dict()
            data["camera"] = src_manager.get_source_by_id(camera_id)
            data["linked_devices"] = dev_manager.get_devices_by_id(
                data["linked_devices"]
            )
            z = detect_manager.add_zone_from_dict(data)
            new_zone = detect_manager.serialize_zone(z)
            new_zone["camera_id"] = camera_id

            return new_zone

        @app.put("/api/zone/{zone_id}")
        async def update_zone(zone_id: str, update: ZoneUpdate):
            for cam_id, zones in self.ZONES.items():
                for z in zones:
                    if z["id"] == zone_id:
                        if update.name is not None:
                            z["name"] = update.name
                        if update.points is not None:
                            if len(update.points) < 3:
                                raise HTTPException(
                                    status_code=400, detail="Минимум 3 точки"
                                )
                            z["points"] = [p.dict() for p in update.points]
                        if update.color is not None:
                            z["color"] = update.color
                        if update.active is not None:
                            z["active"] = update.active
                        if update.linked_devices is not None:
                            for dev_id in update.linked_devices:
                                if dev_id not in self.DEVICES:
                                    raise HTTPException(
                                        status_code=400,
                                        detail=f"Устройство {dev_id} не найдено",
                                    )
                            z["linked_devices"] = update.linked_devices
                        return z
            raise HTTPException(status_code=404, detail="Зона не найдена")

        @app.delete("/api/zone/{zone_id}")
        async def delete_zone(zone_id: str):
            for cam_id, zones in self.ZONES.items():
                for i, z in enumerate(zones):
                    if z["id"] == zone_id:
                        del self.ZONES[cam_id][i]
                        return {"status": "deleted", "id": zone_id}
            raise HTTPException(status_code=404, detail="Зона не найдена")

    def _setup_routes(self):
        app = self.app
        self._setup_site_routes(app)
        self._setup_device_routes(app)
        self._setup_source_routes(app)
        self._setup_zone_routes(app)
        self._setup_system_routes(app)
        self._setup_settings_routes(app)

        # --- WEBSOCKET И КАДРЫ ---
        @app.get("/api/camera/{camera_id}/last-frame")
        async def get_last_frame(camera_id: str):
            manager = self.application_manager.video_source_manager
            s = manager.get_source_by_id(camera_id)
            if s is None:
                raise HTTPException(status_code=404, detail="Камера не найдена")

            last_frame = self._convert_frame(s.get_frame())
            if not last_frame:
                raise HTTPException(status_code=404, detail="Кадр ещё не получен")
            return {"frame": last_frame}

        @app.websocket("/ws/devices")
        async def devices_websocket(websocket: WebSocket):
            await websocket.accept()
            self.ACTIVE_DEVICE_WEBSOCKETS.add(websocket)
            init_msg = json.dumps({
                "type": "devices_init",
                "devices": self.application_manager.device_manager.serialize_devices()
            })
            await websocket.send_text(init_msg)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                print("Клиент отключился от devices websocket")
            except Exception as e:
                print(f"Ошибка WS devices: {e}")
            finally:
                self.ACTIVE_DEVICE_WEBSOCKETS.discard(websocket)
                try:
                    await websocket.close()
                except Exception:
                    pass

        @app.websocket("/ws/{camera_id}")
        async def websocket_endpoint(websocket: WebSocket, camera_id: str):
            await websocket.accept()
            manager = self.application_manager.video_source_manager
            s = manager.get_source_by_id(camera_id)
            det_manager = self.application_manager.detection_manager
            if s is None:
                await websocket.close(code=1008, reason="Camera not found")
                return

            self.ACTIVE_WEBSOCKETS[camera_id] = websocket
            try:
                while True:
                    if s is None:
                        break

                    frame = det_manager.get_last_detected_frame(s)
                    frame_url = self._convert_frame(camera_id, frame)
                    detections_count = random.randint(1, 4)

                    await websocket.send_text(
                        json.dumps(
                            {
                                "frame": frame_url,
                                "detections": detections_count,
                                "timestamp": time.time(),
                            }
                        )
                    )
                    await asyncio.sleep(1 / s.get_fps())
            except WebSocketDisconnect:
                print(f"Клиент отключился от камеры {camera_id}")
            except Exception as e:
                print(f"Ошибка WS камеры {camera_id}: {e}")
            finally:
                if (
                    camera_id in self.ACTIVE_WEBSOCKETS
                    and self.ACTIVE_WEBSOCKETS[camera_id] is websocket
                ):
                    del self.ACTIVE_WEBSOCKETS[camera_id]
                try:
                    print("closing websocket because...")
                    await websocket.close()
                except Exception:
                    pass

    def _generate_frame(self, camera_id: str) -> tuple:
        """Внутренний метод для генерации тестового кадра"""
        cam_data = self.CAMERAS.get(camera_id, {"name": "Unknown Camera"})
        img = Image.new("RGB", (400, 300), color=(25, 25, 35))
        draw = ImageDraw.Draw(img)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((10, 10), f"{cam_data.get('name', 'Camera')}", fill=(0, 255, 0))
        draw.text((10, 30), f"Time: {timestamp}", fill=(200, 200, 200))

        detections_count = random.randint(0, 3)
        for _ in range(detections_count):
            x1, y1 = random.randint(50, 250), random.randint(50, 200)
            x2, y2 = x1 + random.randint(40, 80), y1 + random.randint(60, 120)
            draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=2)
            draw.text(
                (x1, y1 - 15), f"Person {random.randint(85, 99)}%", fill=(0, 255, 0)
            )

        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{img_str}", detections_count

    def _load_fonts(self):
        # 2. Загрузка шрифта с поддержкой кириллицы
        # Укажите путь к .ttf файлу, доступному в вашей ОС или проекте
        font_path = "arial.ttf"  # Windows/macOS
        # Для Linux/Docker: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

        try:
            if os.path.exists(font_path):
                font_large = ImageFont.truetype(font_path, 24)
                font_small = ImageFont.truetype(font_path, 16)
            else:
                # Если файл не найден, пробуем системные пути или fallback
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
        except Exception:
            font_large = font_small = ImageFont.load_default()
        self._font_large = font_large
        self._font_small = font_small

    def _on_device_change(self, device, state, action):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast_device_update(state, action))
        except RuntimeError:
            pass

    async def broadcast_device_update(self, device_data, action):
        msg = json.dumps({"type": "device_update", "device": device_data, "action": action})
        for ws in self.ACTIVE_DEVICE_WEBSOCKETS.copy():
            try:
                await ws.send_text(msg)
            except Exception:
                self.ACTIVE_DEVICE_WEBSOCKETS.discard(ws)

    def _convert_frame(self, camera_id: str, frame: np.ndarray) -> str:
        """Конвертация cv2 кадра в base64 с поддержкой кириллицы"""
        cam_manager = self.application_manager.video_source_manager
        detect_manager = self.application_manager.detection_manager
        cam = cam_manager.get_source_by_id(camera_id)

        # 1. Конвертация BGR (OpenCV) -> RGB (Pillow)
        # Pillow работает в RGB, поэтому цвета нужно корректно преобразовать
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cam_name = cam.name or "Камера"

        font_large = self._font_large
        font_small = self._font_small
        # 3. Отрисовка мета-данных (Pillow рисует от верхнего левого угла)
        draw.text((10, 10), cam_name, font=font_large, fill=(0, 255, 0))
        draw.text(
            (10, 40), f"Время: {timestamp}", font=font_small, fill=(200, 200, 200)
        )

        # 4. Отрисовка детекций
        detections = detect_manager.get_last_detections(cam)
        for d in detections:
            # Приводим координаты к int (модели часто отдают float)
            x1, y1, x2, y2 = map(int, d.box)

            # Рамка
            draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0), width=2)

            # Текст над bounding box
            text_y = max(10, y1 - 20)  # Защита от выхода за верхнюю границу кадра
            confidence = random.randint(85, 99)
            draw.text(
                (x1, text_y),
                f"{d.name} {confidence}%",
                font=font_small,
                fill=(0, 255, 0),
            )

        # 5. Конвертация обратно в BGR и кодирование в JPEG через OpenCV
        img_cv2 = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        success, buffer = cv2.imencode(".jpg", img_cv2)
        if not success:
            raise ValueError("Не удалось закодировать изображение в JPEG")

        img_str = base64.b64encode(buffer.tobytes()).decode("utf-8")
        return f"data:image/jpeg;base64,{img_str}"

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Метод для запуска сервера"""
        import uvicorn

        print(f"🚀 Запуск UI сервера на http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)


# === ТОЧКА ВХОДА ===
if __name__ == "__main__":
    # Можно легко изменить директорию или порт при необходимости
    server = UIServer()
    server.run(host="0.0.0.0", port=8000)
