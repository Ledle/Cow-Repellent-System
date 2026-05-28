import cv2
import logging
from ultralytics import YOLO
from zone import Zone, get_closest_zone
from detector import Detector, Detected
from frame_sender import SyncWSServer
from config_api import ServerConfig
from source import VideoSourceManager, VideoSource
from logger import setup_logging
from callbacks import test_callback, CliCallback

setup_logging()
log = logging.getLogger()

# 2. Классы для отслеживания
# ALLOWED_CLASSES = {"car", "truck", "train", "bus", "cow"}
ALLOWED_CLASSES = {"cow"}
ALLOWED_CLASSES2 = {"car", "truck", "train", "bus", "cow"}

# video_source = "example.mp4"
video_source_url = "rtmp://localhost/live/test"
video_source_url2 = "rtmp://localhost/live/test2"
#video_source_url2 = "http://64.77.205.67/mjpg/video.mjpg?COUNTER"


sender = SyncWSServer()


def callback(detected, frame):
    test_callback(detected, frame, sender)


cli_callback1 = CliCallback("thread 1")
cli_callback2 = CliCallback("thread 2")

config_server = ServerConfig()
source1 = VideoSource(video_source_url, "first source")
source2 = VideoSource(video_source_url2, "second source")
model = YOLO("yolo26m")
model.fuse()


def test_gen():
    cap = cv2.VideoCapture(video_source_url)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        yield frame


# source1.start_reading()
# Инициализация отправщика
detector = Detector(
    model, source1.frame_generator(), cli_callback1.cli_callback, ALLOWED_CLASSES
)
detector2 = Detector(
    model, source2.frame_generator(), cli_callback2.cli_callback, ALLOWED_CLASSES2
)

# sender.start()
# config_server.start()
detector.start_tracking()
detector2.start_tracking()
detector2.thread.join()
