class ResultMock(list):
    pass


class ModelMock:
    def __init__(self, classes: list[str], classes_count: int):
        self.classes = classes
        self.n = classes_count

    def track(self, frame, show=False, stream=True, persist=True):
        res = ResultMock()
        res.extend([ResultMock() for i in range(self.n)])
        res.orig_img = frame
