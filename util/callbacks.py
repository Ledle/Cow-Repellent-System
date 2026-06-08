from objects.detector import Detected
from objects.zone import Zone, get_closest_zone
import cv2
import logging
from objects.source import VideoSource
from objects.device import Device

log = logging.getLogger()
# 3. Координаты зоны контроля
# ZONE2 = Zone.gen_square_zone(0, 0, 300, 300)
ZONE2 = Zone.gen_free_form_zone([0, 0, 300, 300, 0, 300])
ZONE3 = Zone.gen_square_zone(800, 400, 1000, 600)


def zone_to_detection(zone: Zone):
    det = {}
    n = 1
    for c in zone.get_int_coords():
        det[f"x{n}"] = c[0]
        det[f"y{n}"] = c[1]
        n += 1
    det["color"] = "#FA0000" if zone.active else "#00FF00"
    return det


def draw_bbox(frame, box, color, label=None):
    """Рисует прямоугольник и опциональную текстовую метку."""
    x1, y1, x2, y2 = map(int, box)
    thickness = 3 if label else 2
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    if label:
        cv2.putText(
            frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
        )


def test_callback(detected: list[Detected], frame, sender):
    green_zones = {ZONE2, ZONE3}
    red_zones = set()
    for d in detected:
        z = get_closest_zone(d.box, green_zones)
        red_zones.add(z)
    #        draw_bbox(frame, d.box, (0, 255, 0))

    for z in red_zones:
        z.active = True
    for z in green_zones - red_zones:
        z.active = False

    _, encoded_img = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    image_bytes = encoded_img.tobytes()
    detections = [
        {"x": 50, "y": 50, "width": 200, "height": 200, "label": "test"}
    ]  # заглушка
    detections = []
    detections.append(zone_to_detection(ZONE2))
    detections.append(zone_to_detection(ZONE3))
    sender.send(image_bytes, detections)

    # draw_zones(frame, green_zones)
    # cv2.imshow("YOLO Zone Monitor", frame)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #    return True


class DeviceCallback:
    def __init__(
        self,
        devices: list[Device] = [],
        whitelist: list[str] = [],
        blocklist: list[str] = [],
    ):
        self._devices = devices
        self.whitelist = whitelist
        self.blocklist = blocklist
        right_x = 800
        self._zone_devices = {
            Zone.gen_square_zone(0, 0, 100, 600): devices[0],
            Zone.gen_square_zone(right_x, 0, right_x - 100, 600): devices[1],
        }
        self._to_off = {d: 5 for d in self._devices}

    def turn_off_all(self):
        for device in self.devices:
            device.off()
            self._to_off[device] = 5

    def callback(self, detected: list[Detected], frame, source: VideoSource):
        to_enable = []
        for d in detected:
            if d.name in self.whitelist:
                zone = get_closest_zone(d.box, self._zone_devices.keys())
                to_enable.append(self._zone_devices[zone])
            if d.name in self.blocklist:
                log.info(f"обнаружен {d.name}! отключение отпугивателей")
                to_enable.clear()
                break

        for device in self._devices:
            if device in to_enable:
                device.on()
                self._to_off[device] = 5
            else:
                if self._to_off[device] < 1:
                    device.off()
                else:
                    self._to_off[device] -= 1


i = 0


class CliCallback:
    def __init__(self, name: str):
        global i
        self.name = name + str(i)
        i += 1

    def callback(self, detected: list[Detected], frame, source: VideoSource):
        detects = {}
        for d in detected:
            if detects.get(d.name) is None:
                detects[d.name] = 0
            detects[d.name] += 1

        log.info(f"{self.name} | {detects} detected from {source.name}")
        if len(detects) < 1:
            log.info(f"{self.name} | nothing detected from {source.name}")


# 🟦 ВИЗУАЛИЗАЦИЯ ЗОНЫ
def draw_zone_poly(frame, zone_poly, color=(0, 255, 0)):
    cv2.polylines(frame, [zone_poly], isClosed=True, color=color, thickness=2)
    cv2.putText(
        frame,
        "ZONE",
        (zone_poly[0][0], zone_poly[0][1] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2,
    )


def draw_zone(frame, zone: Zone, color=(0, 255, 0)):
    draw_zone_poly(frame, zone.coords, color)


def draw_zones(frame, zones):
    for zone in zones:
        if not zone.active:
            draw_zone(frame, zone, (0, 255, 0))
        else:
            draw_zone(frame, zone, (0, 0, 255))


class ZoneCallback:
    def __init__(
        self,
        devices: list[Device] = [],
        whitelist: list[str] = [],
        blocklist: list[str] = [],
    ):
        self._devices = devices
        self.whitelist = whitelist
        self.blocklist = blocklist
        self._zone_devices: dict[Zone, Device] = dict()
        #self._to_off = {d: 5 for d in self._devices}

    def has_zone(self, zone: Zone):
        return any(zone.id == z.id for z in self._zone_devices.keys())
    def turn_off_all(self):
        for device in self.devices:
            device.off()
            #self._to_off[device] = 5

    def add_zone(self, zone:Zone):
        self._zone_devices[zone]=[]

    def add_device_to_zone(self, zone:Zone, device: Device):
        self._zone_devices[zone].append(device)

    def callback(self, detected: list[Detected], frame, source: VideoSource):
        to_enable = []
        for d in detected:
            if d.name in self.whitelist:
                if self._zone_devices.keys():
                    zone = get_closest_zone(d.box, self._zone_devices.keys())
                    to_enable.extend(self._zone_devices[zone])
            if d.name in self.blocklist:
                log.info(f"обнаружен {d.name}! отключение отпугивателей")
                to_enable.clear()
                break

        log.info(f"devs to enable: {to_enable}")
        for devices in self._zone_devices.values():
            for device in devices:
                if device in to_enable:
                    device.on()
                else:
                    device.off()


