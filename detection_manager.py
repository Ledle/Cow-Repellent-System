import logging
from threading import Thread

from ultralytics import YOLO
from callbacks import DeviceCallback
from detector import Detector
from source import VideoSource
from device import Device
from detector_mock import DetectorMock

log = logging.getLogger("DetectionManager")

ALLOWED_CLASSES = {"car", "truck", "train", "bus", "cow", "man", "human", "person"}
ALLOWED_CLASSES2 = {"cow"}


class DetectionManager:
    def __init__(self, model: YOLO = None):
        self._detectors: dict[str, VideoSource] = dict()
        self.enabled_detectors: set[Detector] = set()
        self.running: bool = False
        self.model = model
        self._devices: dict[str, Device] = dict()
        self.mock = False
        self.mock_delay = 1

    def make_detection(self, source: VideoSource, callback=DeviceCallback):
        if not self.model and not self.mock:
            raise Exception("model is not specified")
        call = callback(
            self._devices[source.name], ["cow"], ["human", "man", "male", "person"]
        )

        if self.mock:
            Detect = DetectorMock
        else:
            Detect = Detector

        if not self._detectors.get(source.name):
            detector = Detect(
                self.model,
                source,
                call.callback,
                ALLOWED_CLASSES,
            )
            self._detectors[source.name] = detector
            if source.enabled:
                self.enabled_detectors.add(detector)

    def set_model(self, model: YOLO):
        self.model = model

    def _get_detection(self, source: VideoSource) -> Detector:
        if not self._detectors.get(source.name):
            self.make_detection()
        return self._detectors.get(source.name)

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

    def assign_device(self, device: Device, source_name: str):
        if self._devices.get(source_name) is None:
            self._devices[source_name] = list()
        self._devices[source_name].append(device)
