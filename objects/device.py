import uuid
import logging
import urllib.request
import urllib.error

log = logging.getLogger("Device")


class Device:
    def __init__(self, name):
        self.id = uuid.uuid4()
        self.name = name if name is not None and len(name) > 0 else self.id
        self.type = "test"
        self._active = False
        self._callbacks = []

    def register_callback(self, callback):
        self._callbacks.append(callback)

    def _notify_callbacks(self):
        state = {
            "id": str(self.id),
            "name": self.name,
            "active": self._active,
            "type": self.type,
        }
        for cb in self._callbacks:
            cb(self, state)

    def on(self):
        log.info(f"device {self.name} activated")
        self._active = True
        self._notify_callbacks()

    def off(self):
        log.info(f"device {self.name} disactivated")
        self._active = False
        self._notify_callbacks()

    def is_active(self):
        return self._active


class HttpDevice(Device):
    def __init__(self, name, on_url="", off_url=""):
        super().__init__(name)
        self.type = "http"
        self.on_url = on_url
        self.off_url = off_url

    def _send_request(self, url):
        if not url:
            return
        try:
            log.info(f"HTTP request -> {url}")
            urllib.request.urlopen(url, timeout=10)
        except urllib.error.URLError as e:
            log.error(f"HTTP request failed for {url}: {e}")
        except Exception as e:
            log.error(f"HTTP request error for {url}: {e}")

    def on(self):
        self._send_request(self.on_url)
        super().on()

    def off(self):
        self._send_request(self.off_url)
        super().off()
