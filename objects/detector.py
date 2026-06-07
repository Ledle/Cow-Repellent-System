import logging
import threading

from ultralytics import YOLO  # type: ignore

from source import VideoSource

log = logging.getLogger("Detector")


class Detected:
    def __init__(self, box, name: str):
        self.box = box
        self.name = name


class Detector:
    def __init__(
        self, model: YOLO, video_source: VideoSource, callback, allowed_classes
    ):
        self.source = video_source
        self._frame_generator = None
        self.current_image = None
        self.current_boxes = set()
        self.callback = callback
        self.allowed_classes = allowed_classes
        self.running = False
        self.model = model

    def track(self, frame):
        return self.model.track(frame, show=False, stream=True, persist=True)

    def _start_tracking(self):
        self.source.start_reading()
        self.source.ready.wait()
        self._frame_generator = self.source.frame_generator()
        while self.running:
            frame = next(self._frame_generator)
            if frame is not None:
                results = self.track(frame)
                self._handle_results(results)
            else:
                log.info("nothing frame, waiting...")

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

            stop = self.callback(detected, frame, self.source)
            if stop:
                self.running = False

    def start_tracking(self):
        self.thread = threading.Thread(target=self._start_tracking)
        log.info(f"thread {self.thread.name} starting...")
        self.running = True
        self.thread.start()

    def pause_tracking(self):
        self.running = False
