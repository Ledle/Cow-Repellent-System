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
        self.ui_server = ui_server or UIServer(self)

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
