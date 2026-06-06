import cv2
import threading
import os
import time

cap = cv2.VideoCapture("test.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
delay = int(1000 / fps)
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "fflags:nobuffer"
print(f"fps: {fps}")


class Che:
    def __init__(self):
        self.fr = None
        self.lock = threading.Lock()
        self.ret = False

    def start(self):
        while True:
            ret, frame = cap.read()
            frame.copy()
            if not ret:
                # Вернуться к началу видео
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            with self.lock:
                self.ret = ret
                self.frame = frame
            time.sleep(1/fps)
            # cv2.imshow("Video", frame)

            # if cv2.waitKey(delay) == 27:
            #    break


c = Che()
tr = threading.Thread(target=c.start)
tr.start()
while True:
    with c.lock:
        if c.ret:
            frame = c.frame
            cv2.imshow("Video", frame)

    if cv2.waitKey(int(delay)) == 27:
        break


cap.release()
cv2.destroyAllWindows()
