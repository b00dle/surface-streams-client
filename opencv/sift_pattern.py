import cv2 as cv
from opencv.pattern import Pattern

SIFT = cv.xfeatures2d.SIFT_create(nfeatures=250)


class SiftPattern(Pattern):
    def __init__(self, pattern_id):
        super().__init__(pattern_id=pattern_id, cv_detector=SIFT)
