import requests
from datetime import datetime
from pprint import pprint
import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, GObject, Gtk, Gdk, GdkX11

SENDER = None
RECEIVER = None


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


def run_udp_pipeline(send_port, receive_port):
    global SENDER, RECEIVER
    from streaming.udp_video_sender import UdpVideoSender
    from streaming.udp_video_receiver import UdpVideoReceiver
    GObject.threads_init()
    Gst.init(None)
    SENDER = UdpVideoSender()
    SENDER.set_port(send_port)

    r = requests.post("http://0.0.0.0:5000/api/clients", data={}, json={
        "in-ip": "0.0.0.0",
        "in-port": 5001,
        "name": "python-client-"+create_timestamp(),
        "out-port": -1
    })
    if r.status_code == 200:
        if r.headers['content-type'] == "application/json":
            data = r.json()
            print("### SUCCESS\n  > data", data)
            print("  > initializing receiver")
            RECEIVER = (data["uuid"], UdpVideoReceiver())
            RECEIVER[1].start(data["out-port"])
        else:
            print("### API error\n > expecting response json")
    else:
        print("### HTTP error\n  > code", r.status_code)
        print("  > reason", r.reason)

    Gtk.main()


def shutdown_udp_pipeline():
    if RECEIVER is not None:
        url = "http://0.0.0.0:5000/api/clients/" + RECEIVER[0]
        r = requests.delete(url)
        if r.status_code == 200:
            print("### SUCCESS\n  > CLEANUP DONE")
        else:
            print("### HTTP error\n  > code", r.status_code)
            print("  > reason", r.reason)


if __name__ == "__main__":
    run_udp_pipeline(5001, 5002)
    shutdown_udp_pipeline()