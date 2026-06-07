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

    def serialize_device(self, device: Device) -> dict:
        """Serialize a Device object to a dictionary."""
        return {
            "id": str(device.id),
            "name": device.name,
        }

    def serialize_devices(self) -> list[dict]:
        """Serialize all devices to a list of dictionaries."""
        return [self.serialize_device(device) for device in self.devices]
