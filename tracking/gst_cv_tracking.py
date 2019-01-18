import numpy as np
import cv2 as cv
import time
from tracking.template_matching import SiftPattern, FlannMatcher

SIFT = cv.xfeatures2d.SIFT_create()
MIN_MATCH_COUNT = 10


class GstCvTracking(object):
    def __init__(self):
        self._flann = FlannMatcher()
        self.patterns = {}
        self._frame_pattern = SiftPattern("THE-FRAME")

    def track(self, image, overlay_result=True):
        """ SIFT/FLANN based object recognition is performed on image.
            frame should be a cv image. Matched patterns can be managed
            using patterns variable of this instance.
            if overlay_result is True then a frame will be drawn
            around objects found. Returns a list of CvTrackingResults. """
        res = []
        self._frame_pattern.set_image(image)
        for pattern in self.patterns.values():
            good = self._flann.knn_match(pattern, self._frame_pattern)
            if len(good) >= MIN_MATCH_COUNT:
                M, mask = self._flann.find_homography(pattern, self._frame_pattern, good)
                res.append(CvTrackingResult(M, mask, pattern.get_id()))
                if overlay_result:
                    pts = pattern.get_shape_points()
                    dst = cv.perspectiveTransform(pts, M)
                    image = cv.polylines(image, [np.int32(dst)], True, 255, 3, cv.LINE_AA)
        return res

    def load_pattern(self, path, pattern_id=None):
        if pattern_id is None:
            pattern_id = path.split("/")[-1]
        self.patterns[pattern_id] = SiftPattern(pattern_id, SIFT)
        # load and compute descriptors only once
        self.patterns[pattern_id].load_image(path)

    def load_patterns(self, paths, pattern_ids=[]):
        if len(paths) != len(pattern_ids):
            pattern_ids = [None for i in range(0, len(paths))]
        for i in range(0, len(paths)):
            self.load_pattern(paths[i], pattern_ids[i])


class CvTrackingResult(object):
    """ Data Transfer object for Tracking Results. """

    def __init__(self, homography=None, mask=None, pattern_id=None):
        self.homography = homography
        self.mask = mask
        self.pattern_id = pattern_id

    def is_valid(self):
        return self.homography is not None and self.mask is not None and self.pattern_id is not None


def test_list_match_video(pattern_paths, video_path):
    tracker = GstCvTracking()
    tracker.load_patterns(pattern_paths)

    # setup video capture
    cap = cv.VideoCapture(
        "filesrc location=\"" + video_path + "\" ! decodebin ! videoconvert ! "
                                             "videoscale ! video/x-raw, width=480, pixel-aspect-ratio=1/1 ! appsink"
    )

    if not cap.isOpened():
        print("Cannot capture test src. Exiting.")
        quit()

    since_print = 0.0
    fps_collection = []
    tracking_res = []
    track_num = 0
    while True:
        start_time = time.time()

        ret, frame = cap.read()
        if ret == False:
            break

        i = 0
        for res in tracker.track(frame):
            if i == track_num:
                img = tracker.patterns[res.pattern_id].get_image().copy()
                w, h, c = frame.shape
                img = cv.warpPerspective(img, res.homography, (h, w))
                cv.imshow("tracked-pattern", img)
            i += 1

        cv.imshow("CVtest", frame)

        elapsed_time = time.time()-start_time
        fps_collection.append(1.0/elapsed_time)
        since_print += elapsed_time
        if since_print > 1.0:
            print("avg fps:", int(sum(fps_collection)/float(len(fps_collection))))
            fps_collection = []
            since_print = 0.0

        key_pressed = cv.waitKey(1) & 0xFF
        if key_pressed == ord('q'):
            break
        elif key_pressed == ord('w'):
            track_num = (track_num + 1) % len(tracker.patterns)