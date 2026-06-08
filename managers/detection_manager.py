import logging
from threading import Thread

from util.callbacks import ZoneCallback
from objects.detector import Detector
from objects.source import VideoSource
from objects.device import Device
from objects.zone import Zone
from mocks.detector_mock import DetectorMock

log = logging.getLogger("DetectionManager")

ALLOWED_CLASSES = {"car", "truck", "train", "bus", "cow", "man", "human", "person"}
ALLOWED_CLASSES2 = {"cow"}


class DetectionManager:
    _zone_i = 1

    def _gen_zone_id(self, suf="zon_"):
        id = self._zone_i
        self._zone_i += 1
        return suf + str(id)

    def __init__(self, model=None):
        self._detectors: dict[str, Detector] = dict()
        self.enabled_detectors: set[Detector] = set()
        self.running: bool = False
        self.model = model
        self._devices: dict[str, Device] = dict()
        self.mock = False
        self.mock_delay = 1
        self._detector_callbacks = dict()
        self._zones_source: dict[Zone, VideoSource] = dict()
        self._zones_devices: dict[Zone, Device] = dict()

    def make_detection(self, source: VideoSource, callback=ZoneCallback):
        if not self.model and not self.mock:
            raise Exception("model is not specified")
        call = callback([], ["cow"], ["human", "man", "male", "person"])

        if self.mock:
            Detect = DetectorMock
        else:
            Detect = Detector

        if not self._detectors.get(source.id):
            detector = Detect(
                self.model,
                source,
                call.callback,
                ALLOWED_CLASSES,
            )
            self._detectors[source.id] = detector
            self._detector_callbacks[detector] = call
            if source.enabled:
                self.enabled_detectors.add(detector)

    def set_model(self, model):
        self.model = model

    def get_source_zones(self,source: VideoSource):
        zones = []
        for z in self._zones_source.keys():
            if self._zones_source.get(z).id is source.id:
                zones.append(z)
        return zones 

    def _get_detection(self, source: VideoSource) -> Detector:
        if not self._detectors.get(source.id):
            self.make_detection()
        return self._detectors.get(source.id)

    def enable_detection(self, source: VideoSource):
        detector = self._get_detection(source)
        self.enabled_detectors.add(detector)
        if detector.running:
            detector.start_tracking()

    def disable_detection(self, source: VideoSource):
        detector = self._get_detection(source)
        self.enabled_detectors.discard(detector)
        if detector.running:
            detector.pause_tracking()

    def start(self):
        self.running = True
        log.debug("manager starting")
        log.debug(f"enabled detectors: {self.enabled_detectors}")
        for d in self.enabled_detectors:
            d.start_tracking()

    def join_trackers(self):
        if not self.running:
            return
        for d in self.enabled_detectors:
            Thread.join(d.thread)

    def add_zone_from_dict(self, data: dict):
        resolution = data["camera"].get_resolution()
        coords = coords_from_points(data["points"], *resolution)
        zone = Zone(coords)
        zone.active = data["active"]
        zone.name = data["name"]
        self.add_zone(zone, data["camera"])
        for d in data["linked_devices"]:
            self.assign_device(d, zone)
        return zone

    def add_zone(self, zone: Zone, source: VideoSource):
        zone.id = self._gen_zone_id()
        detector = self._detectors.get(source.id)
        callback = self._detector_callbacks.get(detector)
        callback.add_zone(zone)
        self._zones_source[zone] = source

    def assign_device(self, device: Device, zone: Zone):
        if self._zones_devices.get(zone) is None:
            self._zones_devices[zone]=[]

        self._zones_devices[zone].append(device)
        for cal in self._detector_callbacks.values():
            if cal.has_zone(zone):
                cal.add_device_to_zone(zone, device)

    def serialize_detector(self, detector: Detector) -> dict:
        """Serialize a Detector object to a dictionary."""
        return {
            "source_name": detector.source.name
            if hasattr(detector, "source") and detector.source
            else None,
            "running": detector.running if hasattr(detector, "running") else False,
            "allowed_classes": list(detector.allowed_classes)
            if hasattr(detector, "allowed_classes")
            else [],
        }

    def serialize_detectors(self) -> list[dict]:
        """Serialize all detectors to a list of dictionaries."""
        return [
            self.serialize_detector(detector) for detector in self._detectors.values()
        ]

    def serialize_device_mapping(self) -> dict:
        """Serialize device mappings to a dictionary."""
        result = {}
        for source_name, devices in self._devices.items():
            result[source_name] = [
                {
                    "id": str(device.id),
                    "name": device.name,
                }
                for device in devices
            ]
        return result

    def serialize_zone(self, zone: Zone) -> dict:
        cam = self._zones_source[zone]
        w, h = cam.get_resolution()
        devices = self._zones_devices.get(zone)
        devices_id = list(map(lambda d: d.id, devices))
        return {
            "id": zone.id,
            "name": zone.name,
            "linked_devices": devices_id,
            "active": zone.active,
            "points": points_from_coords(zone.coords, w, h),
        }
    def serialize_zones(self, zones: list[Zone]) -> list[dict]:
        return [
            self.serialize_zone(z) for z in zones
        ]



def coords_from_points(points: list[dict], width: int, height: int) -> list[int]:
    coords = []
    for p in points:
        coords.append(int(p["x"] * width))
        coords.append(int(p["y"] * height))
    return coords


def points_from_coords(coords: list[int], width: int, height: int) -> list[dict]:
    points = []
    print("coords:")
    print(coords)
    for c in coords:
        point = {"x": c[0] / width, "y": c[1] / height}
        points.append(point)
    return points
