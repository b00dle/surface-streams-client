import numpy as np
import cv2 as cv
import signal
import os
from streaming.cv_video_receiver import CvVideoReceiver
from streaming.subprocess_sender import SubProcessWrapper
from streaming.osc_sender import CvPatternSender
from streaming.osc_pattern import OscPattern
from tracking.gst_cv_tracking import GstCvTracking
from streaming import api_helper

"""
# webcam gst pipeline sinking to udp ports 5002 and 6666
gst-launch-1.0 v4l2src ! decodebin ! videoconvert ! tee name=t ! queue ! videoscale ! video/x-raw, width=320, pixel-aspect-ratio=1/1 ! jpegenc ! rtpgstpay ! udpsink port=5002  t. ! queue ! jpegenc ! rtpgstpay ! udpsink port=6666
"""


class TrackSubProcess(SubProcessWrapper):
    def __init__(self):
        super().__init__()
        self._compute_launch_command()

    def _compute_launch_command(self):
        args = []
        args.append("python")
        args.append(os.path.abspath(__file__))
        self._set_process_args(args)


if __name__ == "__main__":
    PATTERN_PATHS = [
        "/home/basti/Documents/studium/master/surface-streams-client/CLIENT_DATA/207.jpg"
    ]
    PATTERN_MATCH_SCALE = 0.13
    SERVER_IP = "0.0.0.0"
    SERVER_TUIO_PORT = 5001
    FRAME_PORT = 6666
    MATCHING_WIDTH = 640
    PROTOCOL = "jpeg"

    # initialize osc sender
    tuio_sender = CvPatternSender(SERVER_IP, SERVER_TUIO_PORT)
    osc_patterns = {}
    for i in range(0, len(PATTERN_PATHS)):
        p = OscPattern()
        osc_patterns[p.get_s_id()] = p

    # upload images & set uuids
    pattern_ids = []
    p_idx = 0
    for p in osc_patterns.values():
        pattern_ids.append(p.get_s_id())
        uuid = api_helper.upload_image(PATTERN_PATHS[p_idx])
        p.set_uuid(uuid)
        p_idx += 1

    tracker = GstCvTracking()
    tracker.load_patterns(PATTERN_PATHS, pattern_ids, PATTERN_MATCH_SCALE)

    cap = CvVideoReceiver(port=FRAME_PORT, protocol=PROTOCOL, width=MATCHING_WIDTH)

    print_config = True
    visualize = True
    while cap.is_capturing():
        frame = cap.capture()
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
        tuio_sender.send_patterns(upd_patterns)

        if visualize:
            cv.imshow("SurfaceStreams Tracker", frame)

        key_pressed = cv.waitKey(1) & 0xFF
        if key_pressed == ord('q'):
            break

    # cleanup
    cap.release()
    cv.destroyAllWindows()