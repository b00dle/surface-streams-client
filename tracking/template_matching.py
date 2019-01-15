import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import time
from pprint import pprint

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
        "videoscale ! video/x-raw, width=720,pixel-aspect-ratio=1/1 ! appsink"
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
        if len(good) > MIN_MATCH_COUNT:
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

        if matchesMask is not None:
            draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                               singlePointColor=None,
                               matchesMask=matchesMask,  # draw only inliers
                               flags=2)
            matching_summary = cv.drawMatches(img1, kp1, frame, kp2, good, None, **draw_params)
            cv.imshow("CVtest", matching_summary)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break