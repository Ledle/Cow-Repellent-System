import cv2
from zone import *
from detector import Detector, Detected

# 2. Классы для отслеживания
#ALLOWED_CLASSES = {"car", "truck", "train", "bus", "cow"}
ALLOWED_CLASSES = {"cow"}

# 3. Координаты зоны контроля
ZONE2 = Zone(gen_square_zone(0,0,300,300))
ZONE3 = Zone(gen_square_zone(800,400,1000,600))

#video_source = "example.mp4"
video_source = "rtmp://localhost/live/test"

# 🟦 ВИЗУАЛИЗАЦИЯ ЗОНЫ
def draw_zone_poly(frame, zone_poly, color=(0, 255, 0)):
    cv2.polylines(frame, [zone_poly], isClosed=True, color=color, thickness=2)
    cv2.putText(frame, "ZONE", (zone_poly[0][0], zone_poly[0][1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def draw_zone(frame, zone: Zone, color=(0,255,0)):
    draw_zone_poly(frame, zone.coords, color)

# 📦 ПРОВЕРКА: находится ли bounding box внутри зоны
# 🎨 ОТРИСОВКА РАМКИ С УКАЗАНИЕМ ЦВЕТА И ПОДПИСИ
def draw_bbox(frame, box, color, label=None):
    """Рисует прямоугольник и опциональную текстовую метку."""
    x1, y1, x2, y2 = map(int, box)
    thickness = 3 if label else 2
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    if label:
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def draw_zones(frame, zones):
    for zone in zones:
        if not zone.active:
            draw_zone(frame, zone, (0,255,0))
        else:
            draw_zone(frame, zone, (0,0,255))

def callback(detected: list[Detected], frame):
    green_zones = {
            ZONE2,
            ZONE3
        }
    red_zones = set()
    for d in detected:
        z = get_closest_zone(d.box, green_zones)
        red_zones.add(z)
        draw_bbox(frame,d.box,(0,255,0))

    for z in red_zones:
        z.active=True
    for z in green_zones - red_zones:
        z.active=False

    draw_zones(frame, green_zones)
    cv2.imshow("YOLO Zone Monitor", frame)    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return True



# 🚀 Запуск трекинга
print("🟢 Трекинг запущен. Нажмите 'q' в окне видео для выхода.")
detector = Detector("yolo26m",video_source)
detector.start_tracking(callback,ALLOWED_CLASSES)

cv2.destroyAllWindows()
print("🔴 Трекинг остановлен.")
