import numpy as np
import cv2
class Zone:
    def __init__(self, coords):
        self.coords=coords
        self.active=False

def gen_square_zone(x1,y1,x2,y2):
    return np.array([
    [x1, y1],
    [x2, y1],
    [x2, y2],
    [x1, y2]
], dtype=np.int32)

def is_bbox_in_zone(box, zone: Zone):
    """Проверяет попадание центра bbox в полигон зоны."""
    cx = int((box[0] + box[2]) / 2)
    cy = int((box[1] + box[3]) / 2)
    return cv2.pointPolygonTest(zone.coords, (cx, cy), False) >= 0

def get_closest_zone(box, zones):
    cx = int((box[0] + box[2]) / 2)
    cy = int((box[1] + box[3]) / 2)
    return max(zones, key = lambda zone: cv2.pointPolygonTest(zone.coords, (cx, cy), True))

