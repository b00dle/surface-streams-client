import sys
import requests
from datetime import datetime

from processes.surface_streams_receiver import RecvSubProcess
from processes.surface_streams_tracker import TrackSubProcess
from processes.surface_streams_web_cam import WebCamSenderSubProcess


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


class SurfaceStreamsClient(object):
    def __init__(self, my_ip="0.0.0.0", server_ip="0.0.0.0", video_send_port=5002, method="webcam", realsense_dir="./", video_protocol="jpeg"):
        self._my_ip = my_ip
        self._server_ip = server_ip
        self._video_send_port = video_send_port
        self._method = method
        self._realsense_dir = realsense_dir
        self._video_protocol = video_protocol
        self._video_streamer = None
        self._object_streamer = None
        self._stream_receiver = None

    def run(self):
        print(self._method)
        if self._method == "webcam":
            self._run_webcam_stream()
        elif self._method == "realsense":
            print("TODO realsense")
        else:
            raise ValueError("Method '" + self._method + "' not implemented.")
        self.shutdown()

    def _run_webcam_stream(self):
        r = requests.post(
            "http://" + self._server_ip + ":5000/api/clients", data={},
            json={
                "ip": self._my_ip,
                "video_src_port": self._video_send_port,
                "name": "python-client-" + create_timestamp(),
                "video_sink_port": -1,
                "video_protocol": self._video_protocol,
                "tuio_sink_port": -1
            }
        )
        if r.status_code == 200:
            if r.headers['content-type'] == "application/json":
                data = r.json()
                print("### SUCCESS\n  > data", data)
                print("  > initializing receiver")
                print("  > port", data["video_sink_port"])

                self._video_streamer = WebCamSenderSubProcess(
                    server_port=self._video_send_port, my_port=6666,
                    monitor=False
                )
                send_pid = self._video_streamer.start()

                self._object_streamer = TrackSubProcess()
                track_pid = self._object_streamer.start()

                recv = RecvSubProcess(
                    frame_port=data["video_sink_port"], tuio_port=data["tuio_sink_port"],
                    server_ip=self._server_ip, ip=self._my_ip, width=320,
                    video_protocol=data["video_protocol"]
                )
                self._stream_receiver = (data["uuid"], recv)
                recv_pid = self._stream_receiver[1].start()

                ret = self._object_streamer.wait()
                print("SurfaceStreams Object Streamer Process finished with exit code ", ret)

                ret = self._stream_receiver[1].wait()
                print("SurfaceStreams Stream Receiver Process finished with exit code ", ret)
            else:
                print("### API error\n > expecting response json")
        else:
            print("### HTTP error\n  > code", r.status_code)
            print("  > reason", r.reason)

    def shutdown(self):
        if self._method == "webcam":
            self._shutdown_webcam_stream()
        elif self._method == "realsense":
            print("TODO realsense")
        else:
            raise ValueError("Method '" + self._method + "' not implemented.")

    def _shutdown_webcam_stream(self):
        url = "http://" + self._server_ip + ":5000/api/clients/" + self._stream_receiver[0]
        r = requests.delete(url)
        if r.status_code == 200:
            print("### SUCCESS\n  > CLEANUP DONE")
        else:
            print("### HTTP error\n  > code", r.status_code)
            print("  > reason", r.reason)

        try:
            self._object_streamer.stop()
        except OSError:
            print("Object Streamer seems to be already closed.")

        try:
            self._stream_receiver[1].stop()
        except OSError:
            print("Receiver seems to be already closed.")

        try:
            self._video_streamer.stop()
        except OSError:
            print("Sender seems to be already closed.")

'''
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
'''