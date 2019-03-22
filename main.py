import sys
from datetime import datetime
from surface_streams_client import SurfaceStreamsClient

SERVER_CONNECTION = None
VIDEO_STREAMER = None
OBJECT_STREAMER = None
STREAM_RECEIVER = None
MY_IP = "0.0.0.0"       # ip server will send merged video and TUIO stream to
SERVER_IP = "0.0.0.0"   # surface streams server iop
LOCAL_SURFACE = 6666    # local port for accessing surface stream data (used as CV tracking input)
REMOTE_SURFACE = -1     # [-1 means set by server] server port for accessing surface stream data (used for video stream merge)
INPUT = "gstexec"      # choose webcam or gstexec
EXECUTABLE_PATH = "/home/companion/surface-streams/realsense"   # path to executable gst surface
PATTERNS_CONFIG = "CLIENT_DATA/tuio_pattern.json"               # config file containing all tracking patterns
PROTOCOL = "jpeg"                                               # streaming protocol for video stream
PRE_GST_ARGS = ["!"]            # when launching gst executable these are the cmd args inserted before the gstreamer pipe built
WEBCAM_DEVICE = "/dev/video0"   # camera device used for webcam based surface
MIXING_MODE = "other"           # video mixing mode used for logically merging client streams server side (choose 'other' or 'all')
TRACKING_MODE = "local"         # should static objects be tracked ['local', 'remote'], if 'remote' is chosen tracking_ip will determine where to send input surface frames
TRACKING_IP = "0.0.0.0"         # only evaluated if TRACKING_MODE == 'remote'


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


def read_args():
    global MY_IP, SERVER_IP, INPUT, EXECUTABLE_PATH, PROTOCOL, PATTERNS_CONFIG, \
        LOCAL_SURFACE, REMOTE_SURFACE, PRE_GST_ARGS, WEBCAM_DEVICE, MIXING_MODE, \
        TRACKING_MODE, TRACKING_IP

    if len(sys.argv) > 1:
        arg_i = 1
        while arg_i < len(sys.argv):
            arg = sys.argv[arg_i]
            if arg == "-me":
                arg_i += 1
                MY_IP = sys.argv[arg_i]
            elif arg == "-server":
                arg_i += 1
                SERVER_IP = sys.argv[arg_i]
            elif arg == "-input":
                arg_i += 1
                INPUT = sys.argv[arg_i]
                if INPUT == "webcam":
                    next_arg_i = arg_i + 1
                    if next_arg_i < len(sys.argv) and not sys.argv[next_arg_i].startswith("-"):
                        arg_i = next_arg_i
                        WEBCAM_DEVICE = sys.argv[arg_i]
            elif arg == "-execpath":
                arg_i += 1
                EXECUTABLE_PATH = sys.argv[arg_i]
                next_arg_i = arg_i + 1
                if next_arg_i < len(sys.argv) and not sys.argv[next_arg_i].startswith("-"):
                    PRE_GST_ARGS = []
                    while next_arg_i < len(sys.argv) and not sys.argv[next_arg_i].startswith("-"):
                        PRE_GST_ARGS.append(sys.argv[next_arg_i])
                        arg_i = next_arg_i
                        next_arg_i += 1
            elif arg == "-patterns":
                arg_i += 1
                PATTERNS_CONFIG = sys.argv[arg_i]
            elif arg == "-protocol":
                arg_i += 1
                PROTOCOL = sys.argv[arg_i]
            elif arg == "-localsurface":
                arg_i += 1
                LOCAL_SURFACE = int(sys.argv[arg_i])
            elif arg == "-remotesurface":
                arg_i += 1
                REMOTE_SURFACE = int(sys.argv[arg_i])
            elif arg == "-mixing_mode":
                arg_i += 1
                MIXING_MODE = sys.argv[arg_i]
                if MIXING_MODE not in ["all", "other"]:
                    raise ValueError("Mixing mode should be 'all' or 'other'\n  > got"+MIXING_MODE)
            elif arg == "-tracking_mode":
                arg_i += 1
                TRACKING_MODE = sys.argv[arg_i]
                if TRACKING_MODE not in ["local", "remote"]:
                    raise ValueError("Tracking mode should be 'local' or 'remote'\n  > got" + TRACKING_MODE)
            elif arg == "-tracking_ip":
                arg_i += 1
                TRACKING_IP = int(sys.argv[arg_i])
            arg_i += 1

    print("Setting up SurfaceStreams client")
    print("  > My IP:", MY_IP)
    print("  > Server IP:", SERVER_IP)
    print("  > Input:", INPUT)
    print("  > Video Protocol:", PROTOCOL)
    print("  > Executable path:", EXECUTABLE_PATH)
    print("  > Patterns:", PATTERNS_CONFIG)
    print("  > Local surface port:", LOCAL_SURFACE)
    print("  > Remote surface port:", REMOTE_SURFACE)
    print("  > Mixing mode:", MIXING_MODE)
    print("  > Tracking mode:", TRACKING_MODE)
    print("  > Tracking ip:", TRACKING_IP)


def main():
    global MY_IP, SERVER_IP, INPUT, EXECUTABLE_PATH, PROTOCOL, PATTERNS_CONFIG, \
        LOCAL_SURFACE, REMOTE_SURFACE, PRE_GST_ARGS, WEBCAM_DEVICE, MIXING_MODE, \
        TRACKING_MODE, TRACKING_IP

    # read command line arguments
    read_args()

    # run surface streams client using configuration
    client = SurfaceStreamsClient(
        my_ip=MY_IP, server_ip=SERVER_IP, video_send_port=REMOTE_SURFACE,
        input=INPUT, video_protocol=PROTOCOL, executable_path=EXECUTABLE_PATH,
        patterns_config=PATTERNS_CONFIG, surface_port=LOCAL_SURFACE,
        pre_gst_args=PRE_GST_ARGS, webcam_device=WEBCAM_DEVICE,
        mixing_mode=MIXING_MODE, tracking_mode=TRACKING_MODE,
        tracking_ip=TRACKING_IP
    )
    client.run()


if __name__ == "__main__":
    # gst-launch-1.0 filesrc location="/home/companion/Videos/green-sample.mp4" ! decodebin ! videoconvert ! videoscale ! video/x-raw, width=320, pixel-aspect-ratio=1/1 ! jpegenc ! rtpgstpay ! udpsink port=5002
    main()