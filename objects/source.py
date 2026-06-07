import cv2
import threading
import logging
import time
import os


log = logging.getLogger("VideoSource")


class VideoSource:
    def __init__(self, source: str, name: str):
        self.source_url = source
        self.name = name
        self._lock = threading.Lock()
        self.enabled = False
        self._latest_frame = None
        self._cap = None
        self.ready = threading.Event()

    def get_frame(self):
        with self._lock:
            return self._latest_frame

    def _start(self):
        log.debug("source starting")
        cap = self._get_cap()
        while self.enabled:
            ret, frame = cap.read()
            if not ret:
                log.warning(f"unable to read source from {self.source_url}")
                time.sleep(1)
                self.ready.clear()
                continue
                # break
            with self._lock:
                log.debug("frame set")
                self._latest_frame = frame
            if not self.ready.is_set():
                self.ready.set()

    def start_reading(self):
        self.enabled = True
        self.thread = threading.Thread(target=self._start, daemon=True)
        self.thread.start()
        log.debug("source started")

    def stop_reading(self):
        self.enabled = False

    def _get_cap(self):
        if self._cap is None:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "fflags:nobuffer"
            self._cap = cv2.VideoCapture(self.source_url)
        return self._cap

    def release(self):
        self._get_cap.release()

    def frame_generator(self):
        log.debug("frame generating")
        if not self.enabled:
            log.debug("starting reading")
            self.start_reading()
        while self.enabled:
            frame = self.get_frame()
            # log.debug(f"yielding frame... {frame}")
            yield frame
        log.debug("self not running")


def source_from_dict(data: dict) -> VideoSource:
    return VideoSource(data["url"], data["name"])
