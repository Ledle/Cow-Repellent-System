import logging

from objects.device import Device, HttpDevice

log = logging.getLogger("Device")


class DeviceManager:
    _dev_i = 1

    def _gen_dev_id(self, suf="dev_"):
        id = self._dev_i
        self._dev_i += 1
        return suf + str(id)

    def __init__(self, on_change=None):
        self.devices: dict[str, Device] = dict()
        self.enabled_devices: set[Device] = set()
        self.on_change = on_change

    def make_device(self, name, type="test", on_url="", off_url="") -> Device:
        if type == "http":
            device = HttpDevice(name, on_url, off_url)
        else:
            device = Device(name)
        device.id = self._gen_dev_id()
        device.register_callback(self._on_device_active_change)
        self.devices[device.id] = device
        self._notify_change(device, "created")

        return device

    def _on_device_active_change(self, device, state):
        if self.on_change:
            if state["active"]:
                log.info("dev activated!!")
            state["enabled"] = device in self.enabled_devices
            self.on_change(device, state, "updated")

    def _notify_change(self, device, action):
        if self.on_change:
            state = self.serialize_device(device)
            self.on_change(device, state, action)

    def get_devices(self):
        return self.devices

    def serialize_device(self, device: Device) -> dict:
        """Serialize a Device object to a dictionary."""
        result = {
            "id": str(device.id),
            "name": device.name,
            "type": device.type,
            "active": device.is_active(),
            "enabled": device in self.enabled_devices,
        }
        if isinstance(device, HttpDevice):
            result["on_url"] = device.on_url
            result["off_url"] = device.off_url
        return result

    def make_device_from_dict(self, data: dict) -> Device:
        name = data["name"]
        type = data.get("type", "test")
        on_url = data.get("on_url", "")
        off_url = data.get("off_url", "")
        device = self.make_device(name, type, on_url, off_url)
        self._notify_change(device, "created")
        return device

    def serialize_devices(self) -> list[dict]:
        """Serialize all devices to a list of dictionaries."""
        return [self.serialize_device(device) for device in self.devices.values()]

    def get_device_by_id(self, id: str):
        return self.devices.get(id)

    def get_devices_by_id(self, ids: list[str]) -> list[Device]:
        return list(map(self.get_device_by_id, ids))

    def enable_device(self, device: Device):
        self.enabled_devices.add(device)
        self._notify_change(device, "updated")

    def disable_device(self, device: Device):
        self.enabled_devices.discard(device)
        self._notify_change(device, "updated")

    def switch_device(self, device: Device, active: bool):
        if active:
            device.on()
        else:
            device.off()

    def toggle_device(self, device: Device, enable: bool):
        if enable:
            self.enable_device(device)
        else:
            self.disable_device(device)

    def delete_device(self, device):
        self.devices.pop(device.id, None)
        self.enabled_devices.discard(device)
        self._notify_change(device, "deleted")
