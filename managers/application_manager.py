import logging
from .source_manager import VideoSourceManager
from .detection_manager import DetectionManager
from .device_manager import DeviceManager
from datetime import datetime, timedelta

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
    ):
        self.ui=False
        self.video_source_manager = video_source_manager or VideoSourceManager()
        self.detection_manager = detection_manager or DetectionManager()
        self.device_manager = device_manager or DeviceManager()
        self.start_time = datetime.now()

    def get_uptime(self) -> str:
        return self._time_since()
        
    def get_status(self) -> str:
        """
        Dummy method for retrieving the current status of the application.
        Returns a dictionary with status information.
        """
        return "ok"
        #return {
        #    "name": self.get_name(),
        #    "status": "running",
        #    "video_sources_count": len(self.video_source_manager.sources),
        #    "devices_count": len(self.device_manager.devices),
        #    "detection_enabled": self.detection_manager.running,
        #}

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

    def _time_since(self) -> str:
        """
        Возвращает строку с временем, прошедшим с start_time до текущего момента.

        :param start_time: datetime — начальный момент
        :return: str — например "2 days, 3:15:42"
        """
        now = datetime.now()
        delta: timedelta = now - self.start_time

        days = delta.days
        seconds = delta.seconds

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        parts = []
        if days > 0:
            parts.append(f"{days} дн.")
        if hours > 0 or days > 0:
            parts.append(f"{hours} ч.")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes} мин.")
        parts.append(f"{seconds} сек.")

        return " ".join(parts)
