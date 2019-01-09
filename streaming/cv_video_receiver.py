import cv2
import streaming
import os
from streaming.subprocess_sender import SubProcessWrapper

class CvVideoReceiver:
    def __init__(self, port, protocol="jpeg"):
        self._protocol = protocol
        self._port = port
        self._capture = None
        self._pipeline_description = ""
        self._capture_finished = False
        self._init_capture()

    def _init_capture(self):
        self._pipeline_description = "udpsrc port="+str(self._port) + " ! "
        if self._protocol == "jpeg":
            self._pipeline_description += streaming.JPEG_CAPS + " ! queue ! "
            self._pipeline_description += "rtpgstdepay ! "
            self._pipeline_description += "jpegdec ! "
        elif self._protocol == "vp8":
            self._pipeline_description += streaming.VP8_CAPS + " ! queue ! "
            self._pipeline_description += "rtpvp8depay ! "
            self._pipeline_description += "vp8dec ! "
        elif self._protocol == "vp9":
            self._pipeline_description += streaming.VP9_CAPS + " ! queue ! "
            self._pipeline_description += "rtpvp9depay ! "
            self._pipeline_description += "vp9dec ! "
        elif self._protocol == "mp4":
            self._pipeline_description += streaming.MP4_CAPS + " ! queue ! "
            self._pipeline_description += "rtpmp4vdepay ! "
            self._pipeline_description += "avdec_mpeg4 ! "
        elif self._protocol == "h264":
            self._pipeline_description += streaming.H264_CAPS + " ! queue ! "
            self._pipeline_description += "rtph264depay ! "
            self._pipeline_description += "avdec_h264 ! "
        elif self._protocol == "h265":
            self._pipeline_description += streaming.H265_CAPS + " ! queue ! "
            self._pipeline_description += "rtph265depay ! "
            self._pipeline_description += "avdec_h264 ! "
        self._pipeline_description += "videoconvert ! appsink"
        self._capture = cv2.VideoCapture(self._pipeline_description)

    def capture(self):
        """ returns the currently captured frame or None if not capturing. """
        if not self._capture.isOpened():
            print("CvVideoReceiver\n  > Cannot capture from description")
            print(self._pipeline_description)
            return None

        if self._capture_finished:
            print("CvVideoReceiver\n  > capture finished.")
            return None

        ret, frame = self._capture.read()

        if ret == False:
            self._capture_finished = True
            return None

        return frame

    def is_capturing(self):
        return not self._capture_finished


class CvReceiverSubProcess(SubProcessWrapper):
    def __init__(self, port, protocol="jpeg"):
        super().__init__()
        self._port = port
        self._protocol = protocol
        self._compute_launch_command()

    def _compute_launch_command(self):
        args = []
        args.append("python")
        args.append(os.path.abspath(__file__))
        args.append("-port")
        args.append(str(self._port))
        args.append("-protocol")
        args.append(self._protocol)
        self._set_process_args(args)

    def set_port(self, port):
        self._port = port
        self._compute_launch_command()

    def set_protocol(self, protocol):
        self._protocol = protocol
        self._compute_launch_command()


if __name__ == "__main__":
    import sys

    PORT = 5002
    PROTOCOL = "jpeg"

    if len(sys.argv) > 1:
        arg_i = 1
        while arg_i < len(sys.argv):
            arg = sys.argv[arg_i]
            if arg == "-port":
                arg_i += 1
                PORT = int(sys.argv[arg_i])
            elif arg == "-protocol":
                arg_i += 1
                PROTOCOL = sys.argv[arg_i]
            arg_i += 1

    cap = CvVideoReceiver(port=PORT, protocol=PROTOCOL)

    while cap.is_capturing():
        frame = cap.capture()

        cv2.imshow("CvVideoreceiver", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

