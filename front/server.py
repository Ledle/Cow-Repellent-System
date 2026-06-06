import asyncio
import base64
import io
import json
import random
import time
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw

app = FastAPI()

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === PYDANTIC МОДЕЛИ ===


class DeviceCreate(BaseModel):
    name: str
    url: str
    enable: bool = True


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    enable: Optional[bool] = None


class CameraCreate(BaseModel):
    name: str
    url: str
    test: bool = True
    # Добавлены поля для совместимости с фронтендом и генерацией кадров
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
    linked_devices: List[str] = []  # Список ID устройств


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    points: Optional[List[Point]] = None
    color: Optional[str] = None
    active: Optional[bool] = None
    linked_devices: Optional[List[str]] = None


# === MOCK ДАННЫЕ И СЧЕТЧИКИ ===

# Счетчики для генерации ID по аналогии с create_device
device_counter = 3  # Так как dev_01 и dev_02 уже заняты
camera_counter = 3  # Так как cam_01 и cam_02 уже заняты

CAMERAS = {
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

DEVICES = {
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

# Зоны: {camera_id: [zone_dict, ...]}
ZONES = {
    "cam_01": [],
    "cam_02": [],
}

LAST_FRAMES = {}
ACTIVE_WEBSOCKETS = {}


# === HTML СТРАНИЦЫ ===


@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>index.html не найден</h1>"


@app.get("/devices", response_class=HTMLResponse)
async def read_devices():
    try:
        with open("devices.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>devices.html не найден</h1>"


@app.get("/zones", response_class=HTMLResponse)
async def read_zones():
    try:
        with open("zones.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>zones.html не найден</h1>"


# === REST API: УСТРОЙСТВА ===


@app.get("/api/devices")
async def get_devices():
    return list(DEVICES.values())


@app.post("/api/devices")
async def create_device(device: DeviceCreate):
    global device_counter
    dev_id = f"dev_{device_counter:02d}"
    device_counter += 1

    new_device = device.dict()
    new_device["id"] = dev_id
    DEVICES[dev_id] = new_device

    return {"status": "created", "id": dev_id}


@app.put("/api/devices/{device_id}")
async def update_device(device_id: str, device: DeviceUpdate):
    if device_id not in DEVICES:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    d = DEVICES[device_id]
    if device.name is not None:
        d["name"] = device.name
    if device.url is not None:
        d["url"] = device.url
    if device.enable is not None:
        d["enable"] = device.enable

    return {"status": "updated", "id": device_id}


@app.delete("/api/devices/{device_id}")
async def delete_device(device_id: str):
    if device_id not in DEVICES:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    # Удаляем привязки этого устройства из всех зон
    for zones in ZONES.values():
        for z in zones:
            if device_id in z["linked_devices"]:
                z["linked_devices"].remove(device_id)

    del DEVICES[device_id]
    return {"status": "deleted", "id": device_id}


# === REST API: КАМЕРЫ ===


@app.get("/api/system/status")
async def get_system_status():
    camera_list = [
        {"id": cam_id, "name": data["name"]} for cam_id, data in CAMERAS.items()
    ]
    return {
        "name": "VisionGuard Demo 2026",
        "uptime": "14д 2ч 15м",
        "status": "OK",
        "cameras": camera_list,
    }


@app.get("/api/camera/{camera_id}")
async def get_camera(camera_id: str):
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")
    return {"id": camera_id, **CAMERAS[camera_id]}


@app.get("/api/camera/{camera_id}/info")
async def get_camera_info(camera_id: str):
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    cam_data = CAMERAS[camera_id]
    return {
        "socketUrl": f"ws://localhost:8000/ws/{camera_id}",
        "resolution": cam_data.get("resolution", "1920x1080"),
        "fps": cam_data.get("fps", 30),
    }


@app.post("/api/camera")
async def create_camera(camera: CameraCreate):
    global camera_counter

    # Генерация ID по аналогии с create_device
    cam_id = f"cam_{camera_counter:02d}"
    camera_counter += 1

    new_camera = camera.dict()
    CAMERAS[cam_id] = new_camera
    ZONES[cam_id] = []

    return {"status": "created", "id": cam_id}


@app.put("/api/camera/{camera_id}")
async def update_camera(camera_id: str, camera: CameraUpdate):
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    cam_data = CAMERAS[camera_id]
    if camera.name is not None:
        cam_data["name"] = camera.name
    if camera.url is not None:
        cam_data["url"] = camera.url
    if camera.test is not None:
        cam_data["test"] = camera.test
    if camera.resolution is not None:
        cam_data["resolution"] = camera.resolution
    if camera.fps is not None:
        cam_data["fps"] = camera.fps

    return {"status": "updated", "id": camera_id}


@app.delete("/api/camera/{camera_id}")
async def delete_camera(camera_id: str):
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    if camera_id in ACTIVE_WEBSOCKETS:
        try:
            await ACTIVE_WEBSOCKETS[camera_id].close(code=1000, reason="Camera deleted")
        except Exception:
            pass
        del ACTIVE_WEBSOCKETS[camera_id]

    del CAMERAS[camera_id]
    ZONES.pop(camera_id, None)
    LAST_FRAMES.pop(camera_id, None)

    return {"status": "deleted", "id": camera_id}


# === REST API: ЗОНЫ ===


@app.get("/api/camera/{camera_id}/zones")
async def get_zones(camera_id: str):
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    # Обогащаем зоны информацией об устройствах для удобства фронтенда
    zones = ZONES.get(camera_id, [])
    enriched_zones = []
    for z in zones:
        enriched = z.copy()
        enriched["linked_devices_info"] = [
            DEVICES.get(d_id) for d_id in z["linked_devices"] if d_id in DEVICES
        ]
        enriched_zones.append(enriched)

    return enriched_zones


@app.post("/api/camera/{camera_id}/zone")
async def create_zone(camera_id: str, zone: ZoneCreate):
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")
    if len(zone.points) < 3:
        raise HTTPException(status_code=400, detail="Минимум 3 точки")

    # Проверка существования привязанных устройств
    for dev_id in zone.linked_devices:
        if dev_id not in DEVICES:
            raise HTTPException(
                status_code=400, detail=f"Устройство {dev_id} не найдено"
            )

    new_zone = zone.dict()
    new_zone["id"] = str(uuid.uuid4())[:8]
    new_zone["camera_id"] = camera_id

    ZONES.setdefault(camera_id, []).append(new_zone)
    return new_zone


@app.put("/api/zone/{zone_id}")
async def update_zone(zone_id: str, update: ZoneUpdate):
    for cam_id, zones in ZONES.items():
        for z in zones:
            if z["id"] == zone_id:
                if update.name is not None:
                    z["name"] = update.name
                if update.points is not None:
                    if len(update.points) < 3:
                        raise HTTPException(status_code=400, detail="Минимум 3 точки")
                    z["points"] = [p.dict() for p in update.points]
                if update.color is not None:
                    z["color"] = update.color
                if update.active is not None:
                    z["active"] = update.active
                if update.linked_devices is not None:
                    for dev_id in update.linked_devices:
                        if dev_id not in DEVICES:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Устройство {dev_id} не найдено",
                            )
                    z["linked_devices"] = update.linked_devices
                return z

    raise HTTPException(status_code=404, detail="Зона не найдена")


@app.delete("/api/zone/{zone_id}")
async def delete_zone(zone_id: str):
    for cam_id, zones in ZONES.items():
        for i, z in enumerate(zones):
            if z["id"] == zone_id:
                del ZONES[cam_id][i]
                return {"status": "deleted", "id": zone_id}

    raise HTTPException(status_code=404, detail="Зона не найдена")


# === WEBSOCKET И КАДРЫ ===


def generate_frame(camera_id: str) -> tuple:
    cam_data = CAMERAS.get(camera_id, {"name": "Unknown Camera"})
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
        draw.text((x1, y1 - 15), f"Person {random.randint(85, 99)}%", fill=(0, 255, 0))

    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{img_str}", detections_count


@app.websocket("/ws/{camera_id}")
async def websocket_endpoint(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    if camera_id not in CAMERAS:
        await websocket.close(code=1008, reason="Camera not found")
        return

    ACTIVE_WEBSOCKETS[camera_id] = websocket
    try:
        while True:
            if camera_id not in CAMERAS:
                break
            frame_url, detections_count = generate_frame(camera_id)
            LAST_FRAMES[camera_id] = frame_url

            await websocket.send_text(
                json.dumps(
                    {
                        "frame": frame_url,
                        "detections": detections_count,
                        "timestamp": time.time(),
                    }
                )
            )
            await asyncio.sleep(0.15)
    except WebSocketDisconnect:
        print(f"Клиент отключился от камеры {camera_id}")
    except Exception as e:
        print(f"Ошибка WS камеры {camera_id}: {e}")
    finally:
        if camera_id in ACTIVE_WEBSOCKETS and ACTIVE_WEBSOCKETS[camera_id] is websocket:
            del ACTIVE_WEBSOCKETS[camera_id]
        try:
            await websocket.close()
        except Exception:
            pass


@app.get("/api/camera/{camera_id}/last-frame")
async def get_last_frame(camera_id: str):
    if camera_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")
    if not LAST_FRAMES.get(camera_id):
        raise HTTPException(status_code=404, detail="Кадр ещё не получен")
    return {"frame": LAST_FRAMES[camera_id]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
