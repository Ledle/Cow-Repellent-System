import cv2
import threading
import logging
import time
import os
from datetime import datetime


log = logging.getLogger("VideoSource")


class VideoSource:
    def __init__(self, source: str, name: str):
        self.id = None
        self.source_url = source
        self.name = name
        self._lock = threading.Lock()
        self.enabled = False
        self._latest_frame = None
        self._cap = None
        self.ready = threading.Event()
        self._frame_timestamp = datetime.now()

    def get_frame_with_timestamp(self):
        with self._lock:
            return (self._latest_frame, self._frame_timestamp)
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
                self._frame_timestamp = datetime.now()
            if not self.ready.is_set():
                self.ready.set()

    def get_frame_timestamp(self):
        with self._lock:
            return self._frame_timestamp

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
        timestamp = None
        while self.enabled:
            frame,s = self.get_frame_with_timestamp()
            while timestamp == s:
                frame,s = self.get_frame_with_timestamp()
                if timestamp == s:
                    time.sleep(1/self.get_fps())
            timestamp = s
            yield frame
        log.debug("self not running")

    def get_resolution(self):
        width = self._get_cap().get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self._get_cap().get(cv2.CAP_PROP_FRAME_HEIGHT)
        return (width, height)

    def get_fps(self):
        return self._get_cap().get(cv2.CAP_PROP_FPS)


def source_from_dict(data: dict) -> VideoSource:
    return VideoSource(data["url"], data["name"])
