from ultralytics import YOLO

src = "rtmp://localhost/live/test2"
model = YOLO("yolo26s")
model.fuse()
#model.track(source=src,imgsz=(1280,720), show=True)
model.track(source=src, imgsz=240,iou=1, show=True, batch=3)
