import numpy as np
import cv2 as cv
import time
import os
import sys
from streaming.cv_video_receiver import CvVideoReceiver
from streaming.subprocess_sender import SubProcessWrapper
from streaming.osc_sender import CvPatternSender
from streaming.osc_pattern import OscPattern
from tracking.gst_cv_tracking import GstCvTracking
from streaming import api_helper


class TrackSubProcess(SubProcessWrapper):
    def __init__(self, pattern_scale=0.13, server_ip="0.0.0.0", server_tuio_port=5001, frame_port=6666, frame_width=640, frame_protocol="jpeg", patterns_config=""):
        super().__init__()
        self._patterns_config = patterns_config
        self._pattern_scale = pattern_scale
        self._server_ip = server_ip
        self._tuio_port = server_tuio_port
        self._frame_port = frame_port
        self._frame_width = frame_width
        self._frame_protocol = frame_protocol
        self._compute_launch_command()

    def _compute_launch_command(self):
        args = []
        args.append("python")
        args.append(os.path.abspath(__file__))
        if len(self._patterns_config) > 0:
            args.append("-patterns_config")
            args.append(self._patterns_config)
        args.append("-server_ip")
        args.append(self._server_ip)
        args.append("-pattern_scale")
        args.append(str(self._pattern_scale))
        args.append("-tuio_port")
        args.append(str(self._tuio_port))
        args.append("-frame_port")
        args.append(str(self._frame_port))
        args.append("-frame_width")
        args.append(str(self._frame_width))
        args.append("-frame_protocol")
        args.append(self._frame_protocol)
        self._set_process_args(args)


if __name__ == "__main__":
    PATTERN_PATHS = []
    PATTERN_MATCH_SCALE = 0.13
    SERVER_IP = "0.0.0.0"
    SERVER_TUIO_PORT = 5001
    FRAME_PORT = 6666
    MATCHING_WIDTH = 640
    PROTOCOL = "jpeg"
    PATTERNS_CONFIG = ""

    if len(sys.argv) > 1:
        arg_i = 1
        while arg_i < len(sys.argv):
            arg = sys.argv[arg_i]
            if arg == "-patterns_config":
                arg_i += 1
                PATTERNS_CONFIG = sys.argv[arg_i]
                print("Reading Tracking patterns from ", PATTERNS_CONFIG)
                if os.path.isfile(PATTERNS_CONFIG):
                    PATTERN_PATHS = [line.rstrip('\n') for line in open(PATTERNS_CONFIG)]
                    print("  > ", PATTERN_PATHS)
            elif arg == "-pattern_scale":
                arg_i += 1
                PATTERN_MATCH_SCALE = float(sys.argv[arg_i])
            elif arg == "-server_ip":
                arg_i += 1
                SERVER_IP = sys.argv[arg_i]
                api_helper.SERVER_IP = SERVER_IP
            elif arg == "-tuio_port":
                arg_i += 1
                SERVER_TUIO_PORT = int(sys.argv[arg_i])
            elif arg == "-frame_port":
                arg_i += 1
                FRAME_PORT = int(sys.argv[arg_i])
            elif arg == "-frame_width":
                arg_i += 1
                MATCHING_WIDTH = int(sys.argv[arg_i])
            elif arg == "-frame_protocol":
                arg_i += 1
                PROTOCOL = sys.argv[arg_i]
            arg_i += 1

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
    i = 0
    start_time = time.time()
    while cap.is_capturing():
        frame = cap.capture()
        h, w, c = frame.shape

        if print_config:
            print("INITIALIZING Tracking")
            print("  > capture frame size ", w, h)
            print_config = False

        # patterns to send
        upd_patterns = []

        for res in tracker.track_concurrent(frame):
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

        i += 1
        if time.time() - start_time > 1:
            i = 0
            start_time = time.time()

        key_pressed = cv.waitKey(1) & 0xFF
        if key_pressed == ord('q'):
            break

    # cleanup
    cap.release()
    cv.destroyAllWindows()