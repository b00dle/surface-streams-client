import sys
import requests
from datetime import datetime

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


def run_surface_streams(send_port, protocol="jpeg"):
    global VIDEO_STREAMER, OBJECT_STREAMER, STREAM_RECEIVER
    from processes.surface_streams_receiver import RecvSubProcess
    from processes.surface_streams_tracker import TrackSubProcess
    from processes.surface_streams_web_cam import WebCamSenderSubProcess

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

            VIDEO_STREAMER = WebCamSenderSubProcess(
                server_port=send_port, my_port=6666,
                monitor=False
            )
            send_pid = VIDEO_STREAMER.start()

            OBJECT_STREAMER = TrackSubProcess()
            track_pid = OBJECT_STREAMER.start()

            recv = RecvSubProcess(
                frame_port=data["video_sink_port"], tuio_port=data["tuio_sink_port"],
                server_ip=SERVER_IP, ip=MY_IP, width=320, video_protocol=data["video_protocol"]
            )
            STREAM_RECEIVER = (data["uuid"], recv)
            recv_pid = STREAM_RECEIVER[1].start()

            ret = OBJECT_STREAMER.wait()
            print("SurfaceStreams Object Streamer Process finished with exit code ", ret)

            ret = STREAM_RECEIVER[1].wait()
            print("SurfaceStreams Stream Receiver Process finished with exit code ", ret)

            #ret = VIDEO_STREAMER.wait()
            #print("SurfaceStreams Video Streamer Process finished with exit code ", ret)

            shutdown_surface_streams()
        else:
            print("### API error\n > expecting response json")
    else:
        print("### HTTP error\n  > code", r.status_code)
        print("  > reason", r.reason)


def shutdown_surface_streams():
    global VIDEO_STREAMER, OBJECT_STREAMER, STREAM_RECEIVER

    url = "http://" + SERVER_IP +":5000/api/clients/" + STREAM_RECEIVER[0]
    r = requests.delete(url)
    if r.status_code == 200:
        print("### SUCCESS\n  > CLEANUP DONE")
    else:
        print("### HTTP error\n  > code", r.status_code)
        print("  > reason", r.reason)

    try:
        OBJECT_STREAMER.stop()
    except OSError:
        print("Object Streamer seems to be already closed.")

    try:
        STREAM_RECEIVER[1].stop()
    except OSError:
        print("Receiver seems to be already closed.")

    try:
        VIDEO_STREAMER.stop()
    except OSError:
        print("Sender seems to be already closed.")


def run_udp_pipeline(send_port, protocol="jpeg"):
    global VIDEO_STREAMER, STREAM_RECEIVER
    from streaming.udp_video_sender import UdpVideoSender
    from streaming.udp_video_receiver import UdpVideoReceiver
    GObject.threads_init()
    Gst.init(None)
    VIDEO_STREAMER = UdpVideoSender(protocol=protocol)
    VIDEO_STREAMER.set_port(send_port)
    VIDEO_STREAMER.set_host(SERVER_IP)
    #GObject.timeout_add_seconds(1, print_sender_stats)
    #pprint(dir(GObject))
    r = requests.post("http://"+SERVER_IP+":5000/api/clients", data={}, json={
        "ip": MY_IP,
        "video_src_port": send_port,
        "name": "python-client-"+create_timestamp(),
        "video_sink_port": -1,
        "video_protocol": protocol,
        "tuio_sink_port":-1
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


def shutdown_udp_pipeline():
    if STREAM_RECEIVER is not None:
        VIDEO_STREAMER.cleanup()
        url = "http://" + SERVER_IP +":5000/api/clients/" + STREAM_RECEIVER[0]
        r = requests.delete(url)
        if r.status_code == 200:
            print("### SUCCESS\n  > CLEANUP DONE")
        else:
            print("### HTTP error\n  > code", r.status_code)
            print("  > reason", r.reason)


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
    shutdown_udp_pipeline()
    global VIDEO_STREAMER
    VIDEO_STREAMER.stop()
    print("### Realsense process finished with code", VIDEO_STREAMER.return_code)


def run_image_test():
    r = requests.post(
        "http://" + SERVER_IP + ":5000/api/images",
        data={},
        json={"name": "test.png"}
    )
    if r.status_code == 200:
        if r.headers['content-type'] == "application/json":
            data = r.json()
            uuid = data["uuid"]
            print("### SUCCESS\n  > data", data)
            print("  > got image uuid:", uuid)
            print("  > attempting to fill")
            r = requests.put(
                "http://" + SERVER_IP + ":5000/api/images/"+uuid,
                files={'data': open('CLIENT_DATA/test.png', 'rb')}
            )
            if r.status_code == 200:
                print("### SUCCESS")
                print("  > image uploaded")
                r = requests.get(
                    "http://" + SERVER_IP + ":5000/api/images/"+uuid,
                    stream=True
                )
                if r.status_code == 200:
                    content_type = r.headers["content-type"].split("/")
                    if len(content_type) != 2 or content_type[0] != "image":
                        print("### FAILURE\n  > return type is no image")
                    else:
                        print("### SUCCESS")
                        print("  > got image from server")
                        print("  > headers", r.headers["content-type"])
                        with open('CLIENT_DATA/test-from-server.'+content_type[1], 'wb') as img_file:
                            for chunk in r.iter_content(1024):
                                img_file.write(chunk)
                else:
                    print("### HTTP error\n  > code", r.status_code)
                    print("  > reason", r.reason)
            else:
                print("### HTTP error\n  > code", r.status_code)
                print("  > reason", r.reason)
        else:
            print("### API error\n > expecting response json")
    else:
        print("### HTTP error\n  > code", r.status_code)
        print("  > reason", r.reason)


def run_opencv_client(send_port, protocol="jpeg"):
    global VIDEO_STREAMER, STREAM_RECEIVER
    from streaming.udp_video_sender import UdpVideoSender
    from streaming.cv_video_receiver import CvReceiverSubProcess
    GObject.threads_init()
    Gst.init(None)
    VIDEO_STREAMER = UdpVideoSender(protocol=protocol)
    VIDEO_STREAMER.set_port(send_port)
    VIDEO_STREAMER.set_host(SERVER_IP)
    # GObject.timeout_add_seconds(1, print_sender_stats)
    # pprint(dir(GObject))
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
            STREAM_RECEIVER = (data["uuid"], CvReceiverSubProcess(port=data["video_sink_port"], protocol=protocol))
            STREAM_RECEIVER[1].start()
        else:
            print("### API error\n > expecting response json")
    else:
        print("### HTTP error\n  > code", r.status_code)
        print("  > reason", r.reason)

    Gtk.main()


def shutdown_cv_pipeline():
    shutdown_udp_pipeline()
    global STREAM_RECEIVER
    STREAM_RECEIVER[1].stop()
    print("### CvVideoCaptureSubProcess finished with code", STREAM_RECEIVER[1].return_code)


def run_cv_test():
    #print(cv2.getBuildInformation())
    from streaming.cv_video_receiver import CvVideoReceiver
    cap = CvVideoReceiver(5002)
    while cap.is_capturing():
        cap.capture()


def run_asynchoro_test():
    import socket, asyncoro, time, random

    def server_proc(n, sock, coro=None):
        for i in range(n):
            msg, addr = yield sock.recvfrom(1024)
            print('Received "%s" from %s:%s' % (msg, addr[0], addr[1]))
        sock.close()

    def client_proc(host, port, coro=None):
        sock = asyncoro.AsynCoroSocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
        msg = 'client socket: %s' % (sock.fileno())
        print(msg)
        time.sleep(random.randint(1,10))
        yield sock.sendto(msg.encode("utf-8"), (host, port))
        sock.close()

    sock = asyncoro.AsynCoroSocket(socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
    sock.bind(('127.0.0.1', 0))
    host, port = sock.getsockname()

    n = 100
    server_coro = asyncoro.Coro(server_proc, n, sock)
    for i in range(n):
        asyncoro.Coro(client_proc, host, port)


def fill_global_vars():
    global VIDEO_STREAMER, STREAM_RECEIVER, MY_IP, SERVER_IP, METHOD, REALSENSE_DIR, PROTOCOL

    # METHOD = "realsense"
    # METHOD = "filesrc"
    # METHOD = "imagetest"
    METHOD = "surface-streams-2.0"
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
            arg_i += 1

    print("Setting up SurfaceStreams client")
    print("  > My IP:", MY_IP)
    print("  > Server IP:", SERVER_IP)
    print("  > Method:", METHOD)
    print("  > Realsense dir:", REALSENSE_DIR)


def main():
    global VIDEO_STREAMER, STREAM_RECEIVER, MY_IP, SERVER_IP, METHOD, REALSENSE_DIR, PROTOCOL

    fill_global_vars()

    # run each call separately to create 3 clients
    if METHOD == "realsense":
        run_realsense_pipeline(5001, REALSENSE_DIR, PROTOCOL)
        # run_realsense_pipeline(5002, REALSENSE_DIR)
        # run_realsense_pipeline(5003, REALSENSE_DIR)
        shutdown_realsense_pipeline()
    elif METHOD == "filesrc":
        # run_udp_pipeline(5001)
        run_udp_pipeline(5002, PROTOCOL)
        # run_udp_pipeline(5003)
        shutdown_udp_pipeline()
    elif METHOD == "imagetest":
        run_image_test()
    elif METHOD == "cvtest":
        #run_opencv_client(5001, PROTOCOL)
        run_opencv_client(5003, PROTOCOL)
        shutdown_cv_pipeline()
    elif METHOD == "surface-streams-2.0":
        run_surface_streams(5002, PROTOCOL)
        #shutdown_surface_streams_2_0()
    else:
        print("FAILURE")
        print("  > method '" + METHOD + "' not recognized.")


def run_osc_client():
    from streaming import osc_sender
    osc_sender.run_pattern_sender()


def run_osc_server():
    from streaming import osc_receiver
    osc_receiver.run_pattern_receiver()


def run_cv_tracking_sender(ip="127.0.0.1", port=5005, pattern_match_scale=0.18, video_width=480):
    from streaming import cv_tracking_streamer
    from streaming import api_helper
    global SERVER_IP

    fill_global_vars()
    api_helper.SERVER_IP = SERVER_IP

    cv_tracking_streamer.run_sender(
        ip, port,
        pattern_paths=[
            #"CLIENT_DATA/207.jpg",
            'CLIENT_DATA/noble-720w.png',
            'CLIENT_DATA/swamp1-720w.png',
            #'CLIENT_DATA/swamp2-720w.png'
        ],
        video_path='CLIENT_DATA/track.mp4',
        pattern_match_scale=pattern_match_scale,
        video_width=video_width
    )


def run_cv_tracking_receiver(ip="127.0.0.1", tuio_port=5005, frame_port=None):
    from streaming import cv_tracking_streamer
    from streaming import api_helper
    global SERVER_IP

    fill_global_vars()
    api_helper.SERVER_IP = SERVER_IP

    w = 720 * 2
    h = 540 * 2
    cv_tracking_streamer.run_receiver(ip, tuio_port, w, h, frame_port)


if __name__ == "__main__":
    # gst-launch-1.0 filesrc location="/home/companion/Videos/green-sample.mp4" ! decodebin ! videoconvert ! videoscale ! video/x-raw, width=320, pixel-aspect-ratio=1/1 ! jpegenc ! rtpgstpay ! udpsink port=5002
    #run_cv_tracking_sender()
    #run_cv_tracking_receiver(frame_port=None)
    #run_osc_server()
    #run_osc_client()
    #run_tracking_test("video-list-match")
    main()
