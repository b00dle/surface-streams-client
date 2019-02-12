import numpy as np
import cv2 as cv
import os
from processes import ProcessWrapper
from opencv.cv_udp_video_receiver import CvUdpVideoReceiver
from tuio.tuio_receiver import TuioPatternReceiver
from webutils import api_helper


class SurfaceReceiver(ProcessWrapper):
    def __init__(self, frame_port, tuio_port, server_ip, width=640, height=480, ip="0.0.0.0", video_protocol="jpeg", download_folder="CLIENT_DATA/"):
        super().__init__()
        self._frame_port = frame_port
        self._tuio_port = tuio_port
        self._server_ip = server_ip
        self._ip = ip
        self._width = width
        self._height = height
        self._video_protocol = video_protocol
        self._download_folder = download_folder
        self._compute_launch_command()

    def _compute_launch_command(self):
        args = []
        args.append("python")
        args.append(os.path.abspath(__file__))
        args.append("-frame_port")
        args.append(str(self._frame_port))
        args.append("-tuio_port")
        args.append(str(self._tuio_port))
        args.append("-server_ip")
        args.append(str(self._server_ip))
        args.append("-ip")
        args.append(str(self._ip))
        args.append("-video_protocol")
        args.append(str(self._video_protocol))
        args.append("-width")
        args.append(str(self._width))
        args.append("-height")
        args.append(str(self._height))
        args.append("-download_folder")
        args.append(str(self._download_folder))
        self._set_process_args(args)

    def set_port(self, port):
        self._frame_port = port
        self._compute_launch_command()

    def set_protocol(self, protocol):
        self._video_protocol = protocol
        self._compute_launch_command()


if __name__ == "__main__":
    import sys
    import signal
    import time

    IP = "0.0.0.0"
    FRAME_PORT = 5002
    TUIO_PORT = 5003
    PROTOCOL = "jpeg"
    DOWNLOAD_FOLDER = "CLIENT_DATA/"
    W = 640
    H = 480

    if len(sys.argv) > 1:
        arg_i = 1
        while arg_i < len(sys.argv):
            arg = sys.argv[arg_i]
            if arg == "-frame_port":
                arg_i += 1
                FRAME_PORT = int(sys.argv[arg_i])
            elif arg == "-tuio_port":
                arg_i += 1
                TUIO_PORT = int(sys.argv[arg_i])
            elif arg == "-video_protocol":
                arg_i += 1
                PROTOCOL = sys.argv[arg_i]
            elif arg == "-ip":
                arg_i += 1
                IP = sys.argv[arg_i]
            elif arg == "-server_ip":
                arg_i += 1
                api_helper.SERVER_IP = sys.argv[arg_i]
            elif arg == "-w":
                arg_i += 1
                W = int(sys.argv[arg_i])
            elif arg == "-h":
                arg_i += 1
                H = int(sys.argv[arg_i])
            elif arg == "-download_folder":
                arg_i += 1
                DOWNLOAD_FOLDER = sys.argv[arg_i]
            arg_i += 1

    # TUIO based pattern receiver
    tuio_server = TuioPatternReceiver(ip=IP, port=TUIO_PORT, pattern_timeout=1.0)
    tuio_server.start()

    images = {}
    img_paths = []

    cap = CvUdpVideoReceiver(port=FRAME_PORT, protocol=PROTOCOL)

    frame = None
    if cap is None:
        frame = np.zeros((H, W, 3), np.uint8)

    while cap.is_capturing():
        update_log = tuio_server.update_patterns()

        if cap is not None:
            frame = cap.capture()
            H, W, c = frame.shape

        if cap is None:
            frame[:, :] = (0, 0, 0)

        # iterate over all tracked patterns
        for p in tuio_server.get_patterns().values():
            # check next pattern if pattern data not valid
            # can happen if SYM or BND for pattern hasn't been send/received
            if not p.is_valid():
                continue
            uuid = p.get_sym().uuid
            # download image if hasn't been downloaded
            if uuid not in images:
                img_path = api_helper.download_image(uuid, DOWNLOAD_FOLDER)
                if len(img_path) > 0:
                    img_paths.append(img_path)
                    images[uuid] = cv.imread(img_path, -1)
            # draw frame around tracked box
            bnd_s = p.get_bnd().scaled(H, H)
            box = cv.boxPoints((
                (bnd_s.x_pos, bnd_s.y_pos),
                (-bnd_s.width, bnd_s.height),
                bnd_s.angle  # bnd_s.angle if bnd_s.width < bnd_s.height else bnd_s.angle - 90
            ))
            frame = cv.polylines(frame, [np.int32(box)], True, 255, 3, cv.LINE_AA)
            # draw transformed pattern onto frame
            if uuid in images:
                # transform pattern
                img = images[uuid].copy()
                img_h, img_w, img_c = img.shape
                pts = np.float32([[0, 0], [0, img_h - 1], [img_w - 1, img_h - 1], [img_w - 1, 0]]).reshape(-1, 1, 2)
                M = cv.getPerspectiveTransform(pts, box)  # order_points(box))
                frame = cv.warpPerspective(img, M, (W, H), frame, borderMode=cv.BORDER_TRANSPARENT)

        cv.imshow("SurfaceStreams Receiver", frame)

        key_pressed = cv.waitKey(1) & 0xFF
        if key_pressed == ord('q'):
            break

    # cleanup
    cap.release()
    cv.destroyAllWindows()
    tuio_server.terminate()
    # remove temp images
    while len(img_paths) > 0:
        img_path = img_paths[0]
        if os.path.exists(img_path):
            os.remove(img_path)
        img_paths.remove(img_path)
