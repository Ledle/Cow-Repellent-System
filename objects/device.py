import uuid
import logging

log = logging.getLogger("Device")


class Device:
    def __init__(self, name, url=""):
        self.id = uuid.uuid4()
        self.name = name if name is not len(name) > 0 else self.id
        self.url = url
        self._active = False
        self._callbacks = []

    def register_callback(self, callback):
        self._callbacks.append(callback)

    def _notify_callbacks(self):
        state = {"id": str(self.id), "name": self.name, "active": self._active}
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
