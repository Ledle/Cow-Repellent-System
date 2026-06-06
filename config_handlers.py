from ultralytics import YOLO

import detector_mock
from logger import log_levels, setup_logging
from application_manager import ApplicationManager
from typing import Callable
import logging
import threading

log = logging.getLogger("Config")


def camera_config_handler(value: dict, app_manager: ApplicationManager):
    log.debug("handling camera")
    camera, cfgs = app_manager.video_source_manager.get_source_from_dict(value)
    for c in cfgs:
        app_manager.video_source_manager.config_source(camera, c, cfgs[c])
    if value["track"]:
        app_manager.detection_manager.make_detection(camera)


def get_model(name, fuse=True):
    log.info("loading model...")
    model = YOLO(name)
    if fuse:
        model.fuse()
    return model


def model_config_handler(value: dict, app_manager: ApplicationManager):
    if (
        app_manager.detection_manager.model is None
        or app_manager.detection_manager.model.model_name != value["name"]
    ):
        log.debug("handling model")
        if value["test"]:
            app_manager.detection_manager.mock = value["test"]
        else:
            fuse = value.get("fuse") if not value.get("fuse") is None else True
            app_manager.detection_manager.set_model(get_model(value["name"], fuse))
        if value["test_delay"]:
            detector_mock.DELAY = value["test_delay"]


def application_config_handler(value: dict, app_manager: ApplicationManager):
    log.debug("handling app")
    setup_logging(level=log_levels[value["logging_level"]])
    if value["enable_web_ui"]:
        server = threading.Thread(target=app_manager.ui_server.run)
        server.start()


def device_config_handler(value: dict, app_manager: ApplicationManager):
    device = app_manager.device_manager.make_device(value["name"])
    app_manager.detection_manager.assign_device(device, value["camera"])


def handler_build(handler: Callable, app_manager: ApplicationManager) -> Callable:
    return lambda x: handler(x, app_manager)
