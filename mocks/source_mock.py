import logging
import time

import cv2

import objects.source

log = logging.getLogger("VideoSourceMock")


class VideoSourceMock(objects.source.VideoSource):
    i = 0

    def __init__(self, source: str = "test.mp4", name: str = None):
        global i
        if str is None:
            name = "mock" + str(i)
            i += 1
        super().__init__(source, name)
        self.speed = 1

    def _start(self):
        log.debug("mock source starting")
        cap = self._get_cap()
        while self.enabled:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            with self._lock:
                log.debug("frame set")
                self._latest_frame = frame
            if not self.ready.is_set():
                self.ready.set()
            time.sleep(self.fps)

    def _get_cap(self):
        if self._cap is None:
            self._cap = cv2.VideoCapture(self.source_url)
            self.fps = self._cap.get(cv2.CAP_PROP_FPS)
            self.fps *= self.speed
            self.delay = int(1000 / self.fps)
        return self._cap
