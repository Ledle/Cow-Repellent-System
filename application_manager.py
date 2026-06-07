import logging
from source_manager import VideoSourceManager
from detection_manager import DetectionManager
from device_manager import DeviceManager
from ui_server import UIServer

log = logging.getLogger("ApplicationManager")


class ApplicationManager:
    """
    Central manager that contains all other managers and serves as a dependency container.
    """

    def __init__(
        self,
        video_source_manager: VideoSourceManager = None,
        detection_manager: DetectionManager = None,
        device_manager: DeviceManager = None,
        ui_server: UIServer = None,
    ):
        self.video_source_manager = video_source_manager or VideoSourceManager()
        self.detection_manager = detection_manager or DetectionManager()
        self.device_manager = device_manager or DeviceManager()
        self.ui_server = ui_server or UIServer()

    def get_status(self) -> dict:
        """
        Dummy method for retrieving the current status of the application.
        Returns a dictionary with status information.
        """
        return {
            "name": self.get_name(),
            "status": "running",
            "video_sources_count": len(self.video_source_manager.sources),
            "devices_count": len(self.device_manager.devices),
            "detection_enabled": self.detection_manager.running,
        }

    def get_name(self) -> str:
        """
        Dummy method for retrieving the name of the application.
        Returns a string with the application name.
        """
        return "VisionGuard Application"

    def serialize(self) -> dict:
        """Serialize the entire application state to a dictionary."""
        return {
            "name": self.get_name(),
            "status": "running",
            "video_sources": self.video_source_manager.serialize_sources(),
            "devices": self.device_manager.serialize_devices(),
            "detectors": self.detection_manager.serialize_detectors(),
            "device_mappings": self.detection_manager.serialize_device_mapping(),
            "detection_enabled": self.detection_manager.running,
        }