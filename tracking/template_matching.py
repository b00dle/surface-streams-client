import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import time
from pprint import pprint


class SiftPattern(object):
    def __init__(self, pattern_id, cv_sift=None):
        self._id = pattern_id
        self._img = None
        self._key_points = None
        self._descriptors = None
        self._sift = cv_sift

    def get_id(self):
        return self._id

    def get_image(self):
        return self._img

    def get_key_points(self):
        return self._key_points

    def get_descriptors(self):
        return self._descriptors

    def get_shape(self):
        if self.is_empty():
            return None
        return self._img.shape

    def get_shape_points(self):
        if self.is_empty():
            return None
        h, w = self._img.shape
        return np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)

    def load_image(self, file_path, scale=1.0):
        self._img = cv.imread(file_path, 0)
        if scale != 1:
            self._img = cv.resize(self._img, (0,0), fx=scale, fy=scale)
        self._detect_and_compute()

    def set_image(self, img):
        self._img = img
        self._detect_and_compute()

    def is_empty(self):
        return self._img is None

    def _detect_and_compute(self):
        if self.is_empty():
            return
        if self._sift is None:
            self._sift = cv.xfeatures2d.SIFT_create()
        self._key_points, self._descriptors = self._sift.detectAndCompute(self._img, None)


class FlannMatcher(object):
    FLANN_INDEX_KDTREE = 1

    def __init__(self, cv_flann=None):
        self._flann = None
        self._index_params = None
        self._search_params = None
        if cv_flann is not None:
            self._flann = cv_flann
        else:
            self._index_params = dict(algorithm=self.FLANN_INDEX_KDTREE, trees=5)
            self._search_params = dict(checks=50)
            self._flann = cv.FlannBasedMatcher(self._index_params, self._search_params)

    def knn_match(self, pattern, frame):
        """ Returns a list of matched good feature points between pattern and frame.
            Both input parameters are expected to be of type SiftPattern. """
        if pattern.is_empty() or frame.is_empty():
            raise ValueError("pattern and frame cannot be empty.")
        matches = self._flann.knnMatch(
            pattern.get_descriptors(),
            frame.get_descriptors(),
            k=2
        )
        # store all the good matches as per Lowe's ratio test.
        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)
        return good

    def find_homography(self, pattern, frame, good=None):
        """ Returns the Homography to transform points from pattern, to frame.
            Good is a list of matched points retrieved from knn_match.
            If good is empty, knn_match will be called automatically.
            Returns homography M and mask, as per cv2.findHomography(...). """
        if len(good) == 0:
            good = self.knn_match(pattern, frame)
        if pattern.is_empty() or frame.is_empty():
            raise ValueError("pattern and frame cannot be empty.")
        kp1 = pattern.get_key_points()
        kp2 = frame.get_key_points()
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        return cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)


def overlay(img_base, img_overlay):
    x_offset = 50
    y_offset = 50
    y1, y2 = y_offset, y_offset + img_overlay.shape[0]
    x1, x2 = x_offset, x_offset + img_overlay.shape[1]
    alpha_s = img_overlay[:, :, 3] / 255.0
    alpha_l = 1.0 - alpha_s
    for c in range(0, 3):
        img_base[y1:y2, x1:x2, c] = (alpha_s * img_overlay[:, :, c] +
                                  alpha_l * img_base[y1:y2, x1:x2, c])
    return img_base


def test_match_img(pattern_path, frame_path):
    MIN_MATCH_COUNT = 10
    img1 = cv.imread(pattern_path, 0)
    img2 = cv.imread(frame_path, 0)

    # Initiate SIFT detector
    sift = cv.xfeatures2d.SIFT_create()

    start_time = time.time()
    elapsed_times = {}

    # find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1, None)
    elapsed_times["SIFT-pattern"] = time.time() - start_time

    kp2, des2 = sift.detectAndCompute(img2, None)
    elapsed_times["SIFT-find"] = time.time() - start_time - sum(elapsed_times.values())

    FLANN_INDEX_KDTREE = 1

    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)

    flann = cv.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(des1, des2, k=2)

    elapsed_times["Flann"] = time.time() - start_time - sum(elapsed_times.values())

    # store all the good matches as per Lowe's ratio test.
    good = []

    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)

    matchesMask = None

    if len(good) > MIN_MATCH_COUNT:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()
        h, w = img1.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv.perspectiveTransform(pts, M)
        img2 = cv.polylines(img2, [np.int32(dst)], True, 255, 3, cv.LINE_AA)

        elapsed_times["Mask"] = time.time() - start_time - sum(elapsed_times.values())

    else:
        print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
        matchesMask = None

    print("=====TIMES=====")
    pprint(elapsed_times)
    print("> total ", sum(elapsed_times.values()))

    if matchesMask is not None:
        draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                           singlePointColor=None,
                           matchesMask=matchesMask,  # draw only inliers
                           flags=2)
        img3 = cv.drawMatches(img1, kp1, img2, kp2, good, None, **draw_params)
        plt.imshow(img3, 'gray'), plt.show()


def test_match_video(pattern_path, video_path):
    MIN_MATCH_COUNT = 10
    FLANN_INDEX_KDTREE = 1

    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv.FlannBasedMatcher(index_params, search_params)

    img1 = cv.imread(pattern_path, 0)

    # Initiate SIFT detector
    sift = cv.xfeatures2d.SIFT_create()
    kp1, des1 = sift.detectAndCompute(img1, None)

    # setup video capture
    cap = cv.VideoCapture(
        "filesrc location=\"" + video_path + "\" ! decodebin ! videoconvert ! "
        "videoscale ! video/x-raw, width=640, pixel-aspect-ratio=1/1 ! appsink"
    )

    if not cap.isOpened():
        print("Cannot capture test src. Exiting.")
        quit()

    while True:

        ret, frame = cap.read()
        if ret == False:
            break

        kp2, des2 = sift.detectAndCompute(frame, None)
        matches = flann.knnMatch(des1, des2, k=2)

        # store all the good matches as per Lowe's ratio test.
        good = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good.append(m)

        matchesMask = None
        if len(good) >= MIN_MATCH_COUNT:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

            M, mask = cv.findHomography(src_pts, dst_pts, cv.RANSAC, 5.0)
            matchesMask = mask.ravel().tolist()
            h, w = img1.shape
            pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            dst = cv.perspectiveTransform(pts, M)
            frame = cv.polylines(frame, [np.int32(dst)], True, 255, 3, cv.LINE_AA)

        else:
            print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
            matchesMask = None

        '''
        if matchesMask is not None:
            draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                               singlePointColor=None,
                               matchesMask=matchesMask,  # draw only inliers
                               flags=2)
            matching_summary = cv.drawMatches(img1, kp1, frame, kp2, good, None, **draw_params)
            cv.imshow("CVtest", matching_summary)
        '''

        cv.imshow("CVtest", frame)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break


def test_list_match_video(pattern_paths, video_path):
    MIN_MATCH_COUNT = 10
    SIFT = cv.xfeatures2d.SIFT_create()

    flann = FlannMatcher()

    # Init SIFT patterns
    patterns = []
    for path in pattern_paths:
        patterns.append(SiftPattern(path.split("/")[-1], SIFT))
        # load and compute descriptors only once
        patterns[-1].load_image(path)

    # setup video capture
    cap = cv.VideoCapture(
        "filesrc location=\"" + video_path + "\" ! decodebin ! videoconvert ! "
                                             "videoscale ! video/x-raw, width=480, pixel-aspect-ratio=1/1 ! appsink"
    )
    # this sift pattern will hold and evaluate our video frames
    frame_pattern = SiftPattern("VideoFrame", SIFT)

    if not cap.isOpened():
        print("Cannot capture test src. Exiting.")
        quit()


    start_time = time.time()
    since_print = 0.0

    fps_collection = []
    while True:

        start_time = time.time()

        ret, frame = cap.read()
        if ret == False:
            break

        frame_pattern.set_image(frame)

        i = 0
        for pattern in patterns:
            good = flann.knn_match(pattern, frame_pattern)

            matchesMask = None
            if len(good) >= MIN_MATCH_COUNT:
                M, mask = flann.find_homography(pattern, frame_pattern, good)
                matchesMask = mask.ravel().tolist()
                pts = pattern.get_shape_points()
                dst = cv.perspectiveTransform(pts, M)
                frame = cv.polylines(frame, [np.int32(dst)], True, 255, 3, cv.LINE_AA)
                if i == 0:
                    img = pattern.get_image().copy()
                    w, h, c = frame.shape
                    img = cv.warpPerspective(pattern.get_image(), M, (h, w))
                    cv.imshow("warped", img)
            else:
                #print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
                matchesMask = None
            i += 1

        cv.imshow("CVtest", frame)

        elapsed_time = time.time()-start_time
        fps_collection.append(1.0/elapsed_time)
        since_print += elapsed_time
        if since_print > 1.0:
            print("avg fps:", int(sum(fps_collection)/float(len(fps_collection))))
            fps_collection = []
            since_print = 0.0

        if cv.waitKey(1) & 0xFF == ord('q'):
            break