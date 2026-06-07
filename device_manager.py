import logging

from device import Device

log = logging.getLogger("Device")


class DeviceManager:
    def __init__(self):
        self.devices: list[Device] = list()

    def make_device(self, name, url="") -> Device:
        device = Device(name, url)
        self.devices.append(device)
        return device

    def get_devices(self):
        return self.devices
