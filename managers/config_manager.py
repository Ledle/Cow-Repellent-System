import util.config
from typing import Callable


class AppConfigManager:
    def __init__(self, settings: util.config.Settings, callbacks={}):
     
        self._config = settings.model_dump()
        self._callbacks = callbacks

    def set_callback(self, name: str, callback):
        callbacks = self.get_callbacks(name)
        callbacks.append(callback)

    def set(self, name: str, val):
        self._config[name] = val
        self._update(name)

    def update_all(self, priorities: list[str] = None):
        keys = self._config.keys()
        if priorities is not None:
            keys = sort_by_order(keys, priorities)
        for k in keys:
            self._update(k)

    def get_callbacks(self, name) -> list[Callable]:
        if not self._callbacks.get(name):
            self._callbacks[name] = []
        return self._callbacks[name]

    def _update(self, name):
        val = self._config.get(name)
        for c in self.get_callbacks(name):
            if type(val) is list:
                for v in val:
                    c(v)
            else:
                c(val)

    def serialize_config(self) -> dict:
        """Serialize the configuration to a dictionary."""
        return self._config

    def serialize_settings(self) -> dict:
        """Serialize the Pydantic settings model to a dictionary."""
        return self._settings.model_dump()


def sort_by_order(a, b):
    order = {val: i for i, val in enumerate(b)}

    return sorted(a, key=lambda x: order.get(x, len(b)))
