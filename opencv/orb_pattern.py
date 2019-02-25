import cv2 as cv
from opencv.pattern import Pattern

ORB = cv.ORB_create()


class OrbPattern(Pattern):
    def __init__(self, pattern_id):
        super().__init__(pattern_id=pattern_id, cv_detector=ORB)
