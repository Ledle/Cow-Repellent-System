import logging

from objects.device import Device

log = logging.getLogger("Device")


class DeviceManager:
    _dev_i = 1

    def _gen_dev_id(self, suf="dev_"):
        id = self._dev_i
        self._dev_i += 1
        return suf + str(id)

    def __init__(self):
        self.devices: dict[str, Device] = dict()
        self.enabled_devices: set[Device] = set()

    def make_device(self, name, url="") -> Device:
        device = Device(name, url)
        device.id = self._gen_dev_id()
        self.devices[device.id] = device

        return device

    def get_devices(self):
        return self.devices

    def serialize_device(self, device: Device) -> dict:
        """Serialize a Device object to a dictionary."""
        return {
            "id": str(device.id),
            "name": device.name,
        }

    def make_device_from_dict(self, data: dict) -> Device:
        name = data["name"]
        url = data["url"]
        return self.make_device(name, url)

    def serialize_devices(self) -> list[dict]:
        """Serialize all devices to a list of dictionaries."""
        return [self.serialize_device(device) for device in self.devices.values()]

    def get_device_by_id(self, id: str):
        return self.devices.get(id)

    def get_devices_by_id(self, ids: list[str]) -> list[Device]:
        return list(map(self.get_device_by_id, ids))

    def enable_device(self, device: Device):
        self.enabled_devices.add(device)

    def disable_device(self, device: Device):
        self.enabled_devices.discard(device)

    def toggle_device(self, device: Device, enable: bool):
        if enable:
            self.enable_device(device)
        else:
            self.disable_device(device)

    def delete_device(self, device):
        self.devices.pop(device.id)
        self.enabled_devices.discard(device)
