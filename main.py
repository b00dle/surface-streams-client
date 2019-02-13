import sys
from datetime import datetime
from surface_streams_client import SurfaceStreamsClient
from webutils.surface_streams_session import SurfaceStreamsSession

SERVER_CONNECTION = None
VIDEO_STREAMER = None
OBJECT_STREAMER = None
STREAM_RECEIVER = None
MY_IP = "0.0.0.0"
SERVER_IP = "0.0.0.0"
METHOD = "filesrc"
REALSENSE_DIR = "./"
PROTOCOL = "jpeg"


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


def run_realsense_pipeline(send_port, realsense_dir, protocol="jpeg"):
    global VIDEO_STREAMER, STREAM_RECEIVER, SERVER_CONNECTION
    from processes.realsense_surface import RealsenseSurface
    from gstreamer.udp_video_receiver import UdpVideoReceiver
    from webutils import api_helper
    GObject.threads_init()
    Gst.init(None)

    SERVER_CONNECTION = SurfaceStreamsSession(
        my_ip=MY_IP, name="python-client-" + create_timestamp(),
        video_src_port=send_port, video_protocol=protocol
    )

    VIDEO_STREAMER = RealsenseSurface(realsense_dir=realsense_dir, protocol=protocol)
    VIDEO_STREAMER.set_port(send_port)
    VIDEO_STREAMER.set_host(api_helper.SERVER_IP)
    VIDEO_STREAMER.start()

    if SERVER_CONNECTION.connect():
        STREAM_RECEIVER = UdpVideoReceiver(protocol=SERVER_CONNECTION.get_video_protocol())
        STREAM_RECEIVER.start(SERVER_CONNECTION.get_video_sink_port())
        Gtk.main()
    else:
        print("Server connection failed. Aborting.")


def shutdown_realsense_pipeline():
    global STREAM_RECEIVER, VIDEO_STREAMER, SERVER_CONNECTION
    if STREAM_RECEIVER is not None:
        VIDEO_STREAMER.cleanup()
        SERVER_CONNECTION.disconnect()
    VIDEO_STREAMER.stop()
    print("### Realsense process finished with code", VIDEO_STREAMER.return_code)


def read_args():
    global MY_IP, SERVER_IP, METHOD, REALSENSE_DIR, PROTOCOL

    METHOD = "realsense"
    #METHOD = "webcam"
    REALSENSE_DIR = "/home/companion/surface-streams/"
    PROTOCOL = "jpeg"

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
            elif arg == "-realsensedir":
                arg_i += 1
                REALSENSE_DIR = sys.argv[arg_i]
            elif arg == "-protocol":
                arg_i += 1
                PROTOCOL = sys.argv[arg_i]
            arg_i += 1

    print("Setting up SurfaceStreams client")
    print("  > My IP:", MY_IP)
    print("  > Server IP:", SERVER_IP)
    print("  > Method:", METHOD)
    print("  > Video Protocol:", PROTOCOL)
    print("  > Realsense dir:", REALSENSE_DIR)


def main():
    global MY_IP, SERVER_IP, METHOD, REALSENSE_DIR, PROTOCOL

    # read command line arguments
    read_args()

    # run each call separately to create 3 clients
    client = SurfaceStreamsClient(
        my_ip=MY_IP, server_ip=SERVER_IP, video_send_port=5002,
        method=METHOD, video_protocol=PROTOCOL, realsense_dir=REALSENSE_DIR
    )
    client.run()


if __name__ == "__main__":
    # gst-launch-1.0 filesrc location="/home/companion/Videos/green-sample.mp4" ! decodebin ! videoconvert ! videoscale ! video/x-raw, width=320, pixel-aspect-ratio=1/1 ! jpegenc ! rtpgstpay ! udpsink port=5002
    main()