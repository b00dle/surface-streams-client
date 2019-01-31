import numpy as np
import cv2 as cv
import time
import os

from streaming import api_helper
from scipy.spatial import distance as dist
from streaming.osc_sender import CvPatternSender
from streaming.osc_receiver import CvPatternReceiver
from streaming.osc_pattern import OscPattern, OscPatternBnd, OscPatternSym
from tracking.gst_cv_tracking import GstCvTracking


def order_points(pts):
    # sort the points based on their x-coordinates
    xSorted = pts[np.argsort(pts[:, 0]), :]

    # grab the left-most and right-most points from the sorted
    # x-roodinate points
    leftMost = xSorted[:2, :]
    rightMost = xSorted[2:, :]

    # now, sort the left-most coordinates according to their
    # y-coordinates so we can grab the top-left and bottom-left
    # points, respectively
    leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
    (tl, bl) = leftMost

    # now that we have the top-left coordinate, use it as an
    # anchor to calculate the Euclidean distance between the
    # top-left and right-most points; by the Pythagorean
    # theorem, the point with the largest distance will be
    # our bottom-right point
    D = dist.cdist(tl[np.newaxis], rightMost, "euclidean")[0]
    (br, tr) = rightMost[np.argsort(D)[::-1], :]

    # return the coordinates in top-left, top-right,
    # bottom-right, and bottom-left order
    return np.array([tr, tl, bl, br], dtype="float32")


def run_sender(ip, port, pattern_paths, video_path, pattern_match_scale=0.5, video_width=480):
    # initialize osc sender
    sender = CvPatternSender(ip, port)
    osc_patterns = {}
    for i in range(0, len(pattern_paths)):
        p = OscPattern()
        osc_patterns[p.get_s_id()] = p

    # upload images & set uuids
    pattern_ids = []
    p_idx = 0
    for p in osc_patterns.values():
        pattern_ids.append(p.get_s_id())
        uuid = api_helper.upload_image(pattern_paths[p_idx])
        p.set_uuid(uuid)
        p_idx += 1

    tracker = GstCvTracking()
    tracker.load_patterns(pattern_paths, pattern_ids, pattern_match_scale)

    # setup video capture
    '''
    cap = cv.VideoCapture(
        "filesrc location=\"" + video_path + "\" ! decodebin ! videoconvert ! "
        "videoscale ! video/x-raw, width=" + str(video_width) +
        ", pixel-aspect-ratio=1/1 ! appsink"
    )
    '''
    cap = cv.VideoCapture("v4l2src ! videoscale ! video/x-raw, width=" + str(video_width) +
                          ", pixel-aspect-ratio=1/1 ! appsink")


    if not cap.isOpened():
        print("Cannot capture test src. Exiting.")
        quit()

    since_print = 0.0
    fps_collection = []
    print_config = True
    while True:
        start_time = time.time()

        ret, frame = cap.read()
        if ret == False:
            break
        h, w, c = frame.shape

        if print_config:
            print("INITIALIZING Tracking")
            print("  > capture frame size ", w, h)
            print_config = False

        # patterns to send
        upd_patterns = []

        for res in tracker.track(frame):
            # update patterns to send
            osc_patterns[res.pattern_id].set_bnd(res.bnd)
            if osc_patterns[res.pattern_id] not in upd_patterns:
                upd_patterns.append(osc_patterns[res.pattern_id])
            # draw frame around tracked box
            bnd_s = res.bnd.scaled(h, h)
            box = cv.boxPoints((
                (bnd_s.x_pos, bnd_s.y_pos),
                (-bnd_s.width, bnd_s.height),
                bnd_s.angle
            ))
            frame = cv.polylines(frame, [np.int32(box)], True, 255, 3, cv.LINE_AA)

        # send patterns
        sender.send_patterns(upd_patterns)

        cv.imshow("CVtest", frame)

        elapsed_time = time.time() - start_time
        fps_collection.append(1.0 / elapsed_time)
        since_print += elapsed_time
        if since_print > 1.0:
            #print("avg fps:", int(sum(fps_collection) / float(len(fps_collection))))
            fps_collection = []
            since_print = 0.0

        key_pressed = cv.waitKey(1) & 0xFF
        if key_pressed == ord('q'):
            break


def run_receiver(ip, port, w, h, frame_port=None):
    import streaming

    server = CvPatternReceiver(ip, port)
    server.start()

    download_folder = "CLIENT_DATA/"
    images = {}
    img_paths = []

    cap = None
    if frame_port is not None:
        gst_pipe = "udpsrc port=" + str(frame_port) + " ! " + streaming.JPEG_CAPS + \
                   " ! queue ! rtpgstdepay ! jpegdec ! videoconvert ! " \
                   "videoscale ! video/x-raw, width=" + str(w) + \
                   ", pixel-aspect-ratio=1/1 ! appsink"
        cap = cv.VideoCapture(gst_pipe)
        if not cap.isOpened():
            print("Cannot capture from udp. Exiting.")
            quit()

    frame = None
    if cap is None:
        frame = np.zeros((h, w, 3), np.uint8)

    while True:
        update_log = server.update_patterns()

        if cap is not None:
            ret, frame = cap.read()
            h, w, c = frame.shape
            if not ret:
                break

        #if len(update_log["bnd"]) > 0 or len(update_log["sym"]) > 0:
        if cap is None:
            frame[:, :] = (0, 0, 0)

        for p in server.get_patterns().values():
            if not p.is_valid():
                continue
            uuid = p.get_sym().uuid
            # download image
            if uuid not in images:
                img_path = api_helper.download_image(uuid, download_folder)
                if len(img_path) > 0:
                    img_paths.append(img_path)
                    images[uuid] = cv.imread(img_path, -1)
            # draw frame around tracked box
            bnd_s = p.get_bnd().scaled(h, h)
            box = cv.boxPoints((
                (bnd_s.x_pos, bnd_s.y_pos),
                (-bnd_s.width, bnd_s.height),
                bnd_s.angle#bnd_s.angle if bnd_s.width < bnd_s.height else bnd_s.angle - 90
            ))
            frame = cv.polylines(frame, [np.int32(box)], True, 255, 3, cv.LINE_AA)
            # draw transformed pattern
            if uuid in images:
                # transform pattern
                img = images[uuid].copy()
                img_h, img_w, img_c = img.shape
                pts = np.float32([[0, 0], [0, img_h - 1], [img_w - 1, img_h - 1], [img_w - 1, 0]]).reshape(-1, 1, 2)
                M = cv.getPerspectiveTransform(pts, box)#order_points(box))
                frame = cv.warpPerspective(img, M, (w,h), frame, borderMode=cv.BORDER_TRANSPARENT)

        cv.imshow("FRAME", frame)

        key_pressed = cv.waitKey(1) & 0xFF
        if key_pressed == ord('q'):
            break

    # cleanup
    cv.destroyAllWindows()
    server.terminate()
    # remove temp images
    while len(img_paths) > 0:
        img_path = img_paths[0]
        if os.path.exists(img_path):
            os.remove(img_path)
        img_paths.remove(img_path)
