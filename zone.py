import numpy as np
import cv2


class Zone:
    def __init__(self, coords: list[int]):
        self.coords = self._get_np_array(coords)
        self.active = False

    def get_int_coords(self):
        res = []
        for i in self.coords:
            res.append([int(i[0]),int(i[1])])
        return res
    def _get_np_array(self, coords):
        return np.array(
            [[coords[i], coords[i + 1]] for i in range(0, len(coords), 2)],
            dtype=np.int32,
        )

    @classmethod
    def gen_square_zone(self, x1, y1, x2, y2):
        coords = [x1, y1, x2, y1, x2, y2, x1, y2]
        return Zone(coords)

    @classmethod
    def gen_free_form_zone(self, dots: list[int]):
        assert len(dots)%2 == 0
        return Zone(dots)


def is_bbox_in_zone(box, zone: Zone):
    """Проверяет попадание центра bbox в полигон зоны."""
    cx = int((box[0] + box[2]) / 2)
    cy = int((box[1] + box[3]) / 2)
    return cv2.pointPolygonTest(zone.coords, (cx, cy), False) >= 0


def get_closest_zone(box, zones):
    cx = int((box[0] + box[2]) / 2)
    cy = int((box[1] + box[3]) / 2)
    return max(
        zones, key=lambda zone: cv2.pointPolygonTest(zone.coords, (cx, cy), True)
    )
