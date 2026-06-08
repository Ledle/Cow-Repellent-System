import logging
import random

from objects.source import VideoSource
from objects.detector import Detected, Detector
import time

log = logging.getLogger("DetectorMock")

DELAY = 1


class DetectorMock(Detector):
    def __init__(
        self, model, video_source: VideoSource, callback, allowed_classes
    ):
        super().__init__(model, video_source, callback, allowed_classes)
        self.allowed_classes = list(allowed_classes)
        self.class_max_count = 5
        self.last_detections: list[Detected] = []

    def _start_tracking(self):
        self.source.start_reading()
        self.source.ready.wait()
        self._frame_generator = self.source.frame_generator()
        while self.running:
            frame = next(self._frame_generator)
            if frame is not None:
                self._generate_results(frame)
                time.sleep(DELAY)
            else:
                log.info("nothing frame, waiting...")

    def _generate_results(self, frame):
        n = random.randint(0, self.class_max_count)
        detected = []
        for result in range(n):
            class_name = random.choice(self.allowed_classes)
            box = gen_box()
            detected.append(Detected(box, class_name))
        print("setting last detections mock...")
        self.last_detections = detected
        print("last detections: ", self.last_detections)
        stop = self.callback(detected, frame, self.source)
        if stop:
            self.running = False


def gen_box():
    x1 = random.randint(0, 800)
    x2 = random.randint(0, 800)
    y1 = random.randint(0, 800)
    y2 = random.randint(0, 800)
    return [x1, y1, x2, y2]
