import requests
from datetime import datetime
import sys
import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, GObject, Gtk, Gdk, GdkX11

SENDER = None
RECEIVER = None
MY_IP = "0.0.0.0"
SERVER_IP = "0.0.0.0"
METHOD = "filesrc"
REALSENSE_DIR = "./"
PROTOCOL = "jpeg"


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


def run_udp_pipeline(send_port, protocol="jpeg"):
    global SENDER, RECEIVER
    from streaming.udp_video_sender import UdpVideoSender
    from streaming.udp_video_receiver import UdpVideoReceiver
    GObject.threads_init()
    Gst.init(None)
    SENDER = UdpVideoSender(protocol=protocol)
    SENDER.set_port(send_port)
    SENDER.set_host(SERVER_IP)
    #GObject.timeout_add_seconds(1, print_sender_stats)
    #pprint(dir(GObject))
    r = requests.post("http://"+SERVER_IP+":5000/api/clients", data={}, json={
        "in-ip": MY_IP,
        "in-port": send_port,
        "name": "python-client-"+create_timestamp(),
        "out-port": -1,
        "streaming-protocol": protocol
    })
    if r.status_code == 200:
        if r.headers['content-type'] == "application/json":
            data = r.json()
            print("### SUCCESS\n  > data", data)
            print("  > initializing receiver")
            print("  > port", data["out-port"])
            RECEIVER = (data["uuid"], UdpVideoReceiver(protocol=protocol))
            RECEIVER[1].start(data["out-port"])
        else:
            print("### API error\n > expecting response json")
    else:
        print("### HTTP error\n  > code", r.status_code)
        print("  > reason", r.reason)

    Gtk.main()


def shutdown_udp_pipeline():
    if RECEIVER is not None:
        SENDER.cleanup()
        url = "http://"+SERVER_IP+":5000/api/clients/" + RECEIVER[0]
        r = requests.delete(url)
        if r.status_code == 200:
            print("### SUCCESS\n  > CLEANUP DONE")
        else:
            print("### HTTP error\n  > code", r.status_code)
            print("  > reason", r.reason)


def run_realsense_pipeline(send_port, realsense_dir, protocol="jpeg"):
    global SENDER, RECEIVER
    from streaming.subprocess_sender import RealsenseSender
    from streaming.udp_video_receiver import UdpVideoReceiver
    GObject.threads_init()
    Gst.init(None)
    SENDER = RealsenseSender(realsense_dir=realsense_dir, protocol=protocol)
    SENDER.set_port(send_port)
    SENDER.set_host(SERVER_IP)
    SENDER.start()

    r = requests.post("http://" + SERVER_IP + ":5000/api/clients", data={}, json={
        "in-ip": MY_IP,
        "in-port": send_port,
        "name": "python-client-" + create_timestamp(),
        "out-port": -1,
        "streaming-protocol": protocol
    })
    if r.status_code == 200:
        if r.headers['content-type'] == "application/json":
            data = r.json()
            print("### SUCCESS\n  > data", data)
            print("  > initializing receiver")
            print("  > port", data["out-port"])
            RECEIVER = (data["uuid"], UdpVideoReceiver(protocol=protocol))
            RECEIVER[1].start(data["out-port"])
        else:
            print("### API error\n > expecting response json")
    else:
        print("### HTTP error\n  > code", r.status_code)
        print("  > reason", r.reason)

    Gtk.main()


def shutdown_realsense_pipeline():
    shutdown_udp_pipeline()
    global SENDER
    SENDER.stop()
    print("### Realsense process finished with code", SENDER.return_code)


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


def main():
    global SENDER, RECEIVER, MY_IP, SERVER_IP, METHOD, REALSENSE_DIR, PROTOCOL

    #METHOD = "realsense"
    #METHOD = "filesrc"
    METHOD = "imagetest"
    REALSENSE_DIR = "/home/companion/surface-streams/"
    PROTOCOL = "vp9"

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
    else:
        print("FAILURE")
        print("  > method '" + METHOD + "' not recognized.")


if __name__ == "__main__":
    main()
