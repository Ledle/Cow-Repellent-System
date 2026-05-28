import cv2
import threading
import logging


log = logging.getLogger("VideoSource")
log.setLevel(logging.INFO)


class VideoSource:
    def __init__(self, source: str, name: str):
        self.source = source
        self.cap = cv2.VideoCapture(source)
        self.name = name
        self.lock = threading.Lock()
        self.running = False
        self.latest_frame = None

    def get_frame(self):
        # ret, frame = self.cap.read()
        with self.lock:
            return self.latest_frame

    def _start(self):
        log.debug("source starting")
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            with self.lock:
                log.debug("frame set")
                self.latest_frame = frame

    def start_reading(self):
        self.running = True
        self.thread = threading.Thread(target=self._start, daemon=True)
        self.thread.start()
        log.debug("source started")

    def stop_reading(self):
        self.running = False

    def release(self):
        self.cap.release()

    def frame_generator(self):
        log.debug("frame generating")
        if not self.running:
            log.debug("starting reading")
            self.start_reading()
        while self.running:
            frame = self.get_frame()
            #log.debug(f"yielding frame... {frame}")
            yield frame
        log.debug("self not running")


class VideoSourceManager:
    sources = []

    def add_source(self, source: VideoSource):
        self.sources.append(source)
        return self.sources.index(source)

    def frame_generator(self, source_id):
        while self.current_source is None:
            yield self.current_source.get_frame()
