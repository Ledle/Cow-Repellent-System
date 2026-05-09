from ultralytics import YOLO #type: ignore
from zone import *

class Detected:
    def __init__(self, box, name: str):
        self.box=box
        self.name=name

class Detector:
    def __init__(self, model_name: str, video_source: str):
        self.model=YOLO(model_name)
        self.source=video_source
        self.current_image = None
        self.current_boxes = set()

    def track(self):  
        return self.model.track(self.source, show=False, stream=True, persist=True)

    def start_tracking(self, callback, allowed_classes):
        results = self.track()
        for result in results:
            detected=[]
            frame = result.orig_img.copy()
            if result.boxes is not None and len(result.boxes) > 0:
                class_ids = result.boxes.cls.cpu().numpy().astype(int) # type: ignore
                bboxes = result.boxes.xyxy.cpu().numpy() # type: ignore
                for box, cls_id in zip(bboxes, class_ids):
                    class_name = result.names[cls_id]
                    if allowed_classes==None or (class_name in allowed_classes):
                        detected.append(Detected(box,class_name))
            
            stop = callback(detected, frame)
            if stop:
                break

