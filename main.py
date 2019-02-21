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
METHOD = "gstexec"      # choose webcam or gstexec
EXECUTABLE_PATH = "/home/companion/surface-streams/realsense"   # path to executable gst surface
PATTERNS_CONFIG = "CLIENT_DATA/tuio_pattern.txt"                # config file containing all tracking patterns
PROTOCOL = "jpeg"                                               # streaming protocol for video stream


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


def read_args():
    global MY_IP, SERVER_IP, METHOD, EXECUTABLE_PATH, PROTOCOL, PATTERNS_CONFIG, LOCAL_SURFACE, REMOTE_SURFACE

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
            elif arg == "-method":
                arg_i += 1
                METHOD = sys.argv[arg_i]
            elif arg == "-execpath":
                arg_i += 1
                EXECUTABLE_PATH = sys.argv[arg_i]
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
            arg_i += 1

    print("Setting up SurfaceStreams client")
    print("  > My IP:", MY_IP)
    print("  > Server IP:", SERVER_IP)
    print("  > Method:", METHOD)
    print("  > Video Protocol:", PROTOCOL)
    print("  > Executable path:", EXECUTABLE_PATH)
    print("  > Patterns:", PATTERNS_CONFIG)
    print("  > Local surface port:", LOCAL_SURFACE)
    print("  > Remote surface port:", REMOTE_SURFACE)


def main():
    global MY_IP, SERVER_IP, METHOD, EXECUTABLE_PATH, PROTOCOL, PATTERNS_CONFIG, LOCAL_SURFACE, REMOTE_SURFACE

    # read command line arguments
    read_args()

    # run surface streams client using configuration
    client = SurfaceStreamsClient(
        my_ip=MY_IP, server_ip=SERVER_IP, video_send_port=REMOTE_SURFACE,
        method=METHOD, video_protocol=PROTOCOL, executable_path=EXECUTABLE_PATH,
        patterns_config=PATTERNS_CONFIG, surface_port=LOCAL_SURFACE
    )
    client.run()


if __name__ == "__main__":
    # gst-launch-1.0 filesrc location="/home/companion/Videos/green-sample.mp4" ! decodebin ! videoconvert ! videoscale ! video/x-raw, width=320, pixel-aspect-ratio=1/1 ! jpegenc ! rtpgstpay ! udpsink port=5002
    main()