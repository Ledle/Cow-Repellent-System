import logging

from util.config_handlers import (
    handler_build,
    camera_config_handler,
    model_config_handler,
    application_config_handler,
    device_config_handler,
)
from util.config import Settings
from managers.config_manager import AppConfigManager
from util.config_api import WebConfigServer
from util.frame_sender import SyncWSServer
from managers.application_manager import ApplicationManager

settings = Settings()


log = logging.getLogger()

app_manager = ApplicationManager()
sender = SyncWSServer()
config_server = WebConfigServer()

callbacks = {
    "application": [handler_build(application_config_handler, app_manager)],
    "model": [handler_build(model_config_handler, app_manager)],
    "camera": [handler_build(camera_config_handler, app_manager)],
    "repeller": [handler_build(device_config_handler, app_manager)],
}
callbacks_priority = ["application", "model", "repeller", "camera"]

config_manager = AppConfigManager(settings, callbacks)
config_manager.update_all(callbacks_priority)
app_manager.detection_manager.start()
app_manager.detection_manager.join_trackers()
