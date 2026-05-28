from ultralytics import YOLO  # type: ignore
from zone import *
import threading
import logging


log = logging.getLogger()


class Detected:
    def __init__(self, box, name: str):
        self.box = box
        self.name = name


class Detector:
    def __init__(self, model: YOLO, video_source, callback, allowed_classes):
        self.model = model
        self.source = video_source
        self.current_image = None
        self.current_boxes = set()
        self.callback = callback
        self.allowed_classes = allowed_classes
        self.running = False

    def track(self, frame):
        return self.model.track(frame, show=False, stream=True, persist=True)

    def _start_tracking(self):
        while self.running:
            frame = next(self.source)
            results = self.track(frame)
            self._handle_results(results)

    def _handle_results(self, results):
        for result in results:
            detected = []
            frame = result.orig_img.copy()
            if result.boxes is not None and len(result.boxes) > 0:
                class_ids = result.boxes.cls.cpu().numpy().astype(int)  # type: ignore
                bboxes = result.boxes.xyxy.cpu().numpy()  # type: ignore
                for box, cls_id in zip(bboxes, class_ids):
                    class_name = result.names[cls_id]
                    if (self.allowed_classes is None) or (
                        class_name in self.allowed_classes
                    ):
                        detected.append(Detected(box, class_name))

            stop = self.callback(detected, frame)
            if stop:
                break

    def start_tracking(self):
        self.thread = threading.Thread(target=self._start_tracking)
        self.running = True
        self.thread.start()
        log.info(f"thread {self.thread.name} started")
