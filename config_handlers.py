from ultralytics import YOLO

import detector_mock
from logger import log_levels, setup_logging
from source_manager import VideoSourceManager
from detection_manager import DetectionManager
from device_manager import DeviceManager
from typing import Callable
import logging
from ui_server import UIServer
import threading

log = logging.getLogger("Config")


def camera_config_handler(
    value: dict, camera_manager: VideoSourceManager, detection_manager: DetectionManager
):
    log.debug("handling camera")
    camera, cfgs = camera_manager.get_source_from_dict(value)
    for c in cfgs:
        camera_manager.config_source(camera, c, cfgs[c])
    if value["track"]:
        detection_manager.make_detection(camera)


def get_model(name, fuse=True):
    log.info("loading model...")
    model = YOLO(name)
    if fuse:
        model.fuse()
    return model


def model_config_handler(value: dict, detection_manager: DetectionManager):
    if (
        detection_manager.model is None
        or detection_manager.model.model_name != value["name"]
    ):
        log.debug("handling model")
        if value["test"]:
            detection_manager.mock = value["test"]
        else:
            fuse = value.get("fuse") if not value.get("fuse") is None else True
            detection_manager.set_model(get_model(value["name"], fuse))
        if value["test_delay"]:
            detector_mock.DELAY = value["test_delay"]


def application_config_handler(value: dict, ui_server: UIServer):
    log.debug("handling app")
    setup_logging(level=log_levels[value["logging_level"]])
    if value["enable_web_ui"]:
        server = threading.Thread(target=ui_server.run)
        server.start()


def device_config_handler(
    value: dict, device_manager: DeviceManager, detection_manager: DetectionManager
):
    device = device_manager.make_device(value["name"])
    detection_manager.assign_device(device, value["camera"])


def handler_build(handler: Callable, *deps) -> Callable:
    return lambda x: handler(x, *deps)
