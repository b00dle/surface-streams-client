import cv2 as cv
from opencv.pattern import Pattern

SURF = cv.xfeatures2d.SURF_create()


class SurfPattern(Pattern):
    def __init__(self, pattern_id):
        super().__init__(pattern_id=pattern_id, cv_detector=SURF)
