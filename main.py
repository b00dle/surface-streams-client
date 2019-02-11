import sys
import requests
from datetime import datetime

from surface_streams_client import SurfaceStreamsClient

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
    global VIDEO_STREAMER, STREAM_RECEIVER
    from streaming.subprocess_sender import RealsenseSender
    from streaming.udp_video_receiver import UdpVideoReceiver
    GObject.threads_init()
    Gst.init(None)
    VIDEO_STREAMER = RealsenseSender(realsense_dir=realsense_dir, protocol=protocol)
    VIDEO_STREAMER.set_port(send_port)
    VIDEO_STREAMER.set_host(SERVER_IP)
    VIDEO_STREAMER.start()

    r = requests.post("http://" + SERVER_IP + ":5000/api/clients", data={}, json={
        "ip": MY_IP,
        "video_src_port": send_port,
        "name": "python-client-" + create_timestamp(),
        "video_sink_port": -1,
        "video_protocol": protocol,
        "tuio_sink_port": -1
    })
    if r.status_code == 200:
        if r.headers['content-type'] == "application/json":
            data = r.json()
            print("### SUCCESS\n  > data", data)
            print("  > initializing receiver")
            print("  > port", data["video_sink_port"])
            STREAM_RECEIVER = (data["uuid"], UdpVideoReceiver(protocol=protocol))
            STREAM_RECEIVER[1].start(data["video_sink_port"])
        else:
            print("### API error\n > expecting response json")
    else:
        print("### HTTP error\n  > code", r.status_code)
        print("  > reason", r.reason)

    Gtk.main()


def shutdown_realsense_pipeline():
    if STREAM_RECEIVER is not None:
        VIDEO_STREAMER.cleanup()
        url = "http://" + SERVER_IP +":5000/api/clients/" + STREAM_RECEIVER[0]
        r = requests.delete(url)
        if r.status_code == 200:
            print("### SUCCESS\n  > CLEANUP DONE")
        else:
            print("### HTTP error\n  > code", r.status_code)
            print("  > reason", r.reason)
    global VIDEO_STREAMER
    VIDEO_STREAMER.stop()
    print("### Realsense process finished with code", VIDEO_STREAMER.return_code)


def read_args():
    global MY_IP, SERVER_IP, METHOD, REALSENSE_DIR, PROTOCOL

    # METHOD = "realsense"
    METHOD = "webcam"
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
    if METHOD == "realsense":
        run_realsense_pipeline(5001, REALSENSE_DIR, PROTOCOL)
        # run_realsense_pipeline(5002, REALSENSE_DIR)
        # run_realsense_pipeline(5003, REALSENSE_DIR)
        shutdown_realsense_pipeline()
    elif METHOD == "webcam":
        client = SurfaceStreamsClient(
            my_ip=MY_IP, server_ip=SERVER_IP, video_send_port=5002,
            method="webcam", video_protocol=PROTOCOL
        )
        client.run()
    else:
        print("FAILURE")
        print("  > method '" + METHOD + "' not recognized.")


if __name__ == "__main__":
    # gst-launch-1.0 filesrc location="/home/companion/Videos/green-sample.mp4" ! decodebin ! videoconvert ! videoscale ! video/x-raw, width=320, pixel-aspect-ratio=1/1 ! jpegenc ! rtpgstpay ! udpsink port=5002
    main()