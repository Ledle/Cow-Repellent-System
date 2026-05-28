from ultralytics import YOLO  # type: ignore
import cv2
import threading
import time

source1 = "http://64.77.205.67/mjpg/video.mjpg?COUNTER"
source2 = "http://210.249.39.229/mjpg/video.mjpg?COUNTER"
source3 = "rtmp://localhost/live/test"


class LatestFrameGrabber:
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.latest_frame = None
        self.lock = threading.Lock()
        self.running = True

        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def _reader(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            with self.lock:
                self.latest_frame = frame

    def get_frame(self):
        with self.lock:
            return self.latest_frame

    def release(self):
        self.running = False
        self.cap.release()


class CameraProcessor:
    def __init__(self, source: str, model: YOLO, window_name: str = None):
        self.source = source
        self.model = model
        self.window_name = window_name

        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._process, daemon=True)
        self.thread.start()
        print(f"thread {self.thread.name} ({self.source}) started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        #self.cap.release()
        self.grabber.release()
        if (
            self.window_name
            and cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) >= 0
        ):
            cv2.destroyWindow(self.window_name)

    def _process(self):
        self.grabber = LatestFrameGrabber(self.source)
        while self.running:
            #ret, frame = self.cap.read()
            #if not ret:
            #    time.sleep(0.1)  # Избегаем 100% загрузки CPU при отключении камеры
            #    continue
            frame = self.grabber.get_frame()

            # Трекинг: persist=True сохраняет состояние трекера между кадрами
            print(f"thread {self.thread.name} tracking...")
            results = self.model.track(
                frame,
                persist=True,
                verbose=False,
                conf=0.4,
                iou=0.45,
                device="cpu",  # 0 для GPU, 'cpu' для процессора
            )
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)  # type: ignore
            for c in class_ids:
                print(f"{self.thread.name} found {results[0].names[c]}")
            print(f"thread {self.thread.name} ended tracking")

# ---------------- НАСТРОЙКА ----------------
# Загрузите модель один раз. Ultralytics кеширует веса, потоки будут использовать одну модель.
model = YOLO("yolo26m.pt")  # или yolov8s.pt, yolov10m.pt и т.д.
model.fuse()

processors = []
for i, src in enumerate([source1, source2, source3]):
    proc = CameraProcessor(src, model, window_name=f"Cam_{i}")
    processors.append(proc)
    proc.start()

# Главный поток держит приложение alive
try:
    while any(p.running for p in processors):
        time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    for p in processors:
        p.stop()
    # cv2.destroyAllWindows()
