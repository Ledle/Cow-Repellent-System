import mocks.detector_mock
from .logger import log_levels, setup_logging
from managers.application_manager import ApplicationManager
from typing import Callable
import logging

log = logging.getLogger("Config")


def camera_config_handler(value: dict, app_manager: ApplicationManager):
    log.debug("handling camera")
    src_manager = app_manager.video_source_manager
    id = src_manager.create_source_from_dict(value)
    camera = src_manager.get_source_by_id(id)
    if value["track"]:
        app_manager.detection_manager.make_detection(camera)


def get_model(name, fuse=True):
    from ultralytics import YOLO
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
            mocks.detector_mock.DELAY = value["test_delay"]
        app_manager.detection_manager.model_verbose = value["verbose"]


def application_config_handler(value: dict, app_manager: ApplicationManager):
    log.debug("handling app")
    setup_logging(level=log_levels[value["logging_level"]])
    app_manager.ui = value["enable_web_ui"] or False
     


def device_config_handler(value: dict, app_manager: ApplicationManager):
    device_manager = app_manager.device_manager
    device = device_manager.make_device(
        value["name"],
        type=value.get("type", "test"),
        on_url=value.get("on_url", ""),
        off_url=value.get("off_url", ""),
    )
    device_manager.toggle_device(device, value.get("enabled", True))
    app_manager.detection_manager.assign_device(device, value["camera"])


def handler_build(handler: Callable, app_manager: ApplicationManager) -> Callable:
    return lambda x: handler(x, app_manager)
