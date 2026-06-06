import logging

from config_handlers import (
    handler_build,
    camera_config_handler,
    model_config_handler,
    application_config_handler,
    device_config_handler,
)
from config import Settings
from config_manager import AppConfigManager
from config_api import WebConfigServer
from frame_sender import SyncWSServer
from source_manager import VideoSourceManager
from detection_manager import DetectionManager
from device_manager import DeviceManager
from ui_server import UIServer

settings = Settings()


log = logging.getLogger()

camera_manager = VideoSourceManager()
detection_manager = DetectionManager()
sender = SyncWSServer()
config_server = WebConfigServer()
device_manager = DeviceManager()
ui_server = UIServer()

callbacks = {
    "application": [handler_build(application_config_handler, ui_server)],
    "model": [handler_build(model_config_handler, detection_manager)],
    "camera": [handler_build(camera_config_handler, camera_manager, detection_manager)],
    "repeller": [
        handler_build(device_config_handler, device_manager, detection_manager)
    ],
}
callbacks_priority = ["application", "model", "repeller", "camera"]

config_manager = AppConfigManager(settings, callbacks)
config_manager.update_all(callbacks_priority)
detection_manager.start()
detection_manager.join_trackers()
