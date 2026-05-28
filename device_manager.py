import uuid
import logging

log = logging.getLogger("Device")


class Device:
    def __init__(self, name, url=""):
        self.id = uuid.UUID()
        self.name = name if name is not len(name) > 0 else self.id

    def on(self):
        log.info(f"device {self.name} activated")

    def off(self):
        log.info(f"device {self.name} disactivated")
