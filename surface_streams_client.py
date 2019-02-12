from datetime import datetime

from processes.surface_receiver import SurfaceReceiver
from processes.surface_tracker import SurfaceTracker
from processes.webcam_surface import WebcamSurface
from webutils.surface_streams_session import SurfaceStreamsSession
from webutils import api_helper


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


class SurfaceStreamsClient(object):
    def __init__(self, my_ip="0.0.0.0", server_ip="0.0.0.0", video_send_port=5002, method="webcam", realsense_dir="./", video_protocol="jpeg"):
        api_helper.SERVER_IP = server_ip
        self._method = method
        self._realsense_dir = realsense_dir
        self._session = SurfaceStreamsSession(
            my_ip=my_ip, name="python-client-" + create_timestamp(),
            video_src_port=video_send_port, video_protocol=video_protocol
        )
        # will be filled upon run (depending on set method)
        self._stream_receiver = None
        self._video_streamer = None
        self._object_streamer = None

    def run(self):
        print("METHOD:", self._method)
        if self._method == "webcam":
            self._run_webcam_stream()
        elif self._method == "realsense":
            print("TODO realsense")
        else:
            raise ValueError("Method '" + self._method + "' not implemented.")
        self.shutdown()

    def _run_webcam_stream(self):
        # connect to surface streams server
        if self._session.connect():
            # initialize video streamer, object streamer and stream receiver
            self._video_streamer = WebcamSurface(
                server_port=self._session.get_video_src_port(), my_port=6666,
                monitor=False
            )
            self._object_streamer = SurfaceTracker(
                server_ip=api_helper.SERVER_IP, server_tuio_port=5001,
                frame_port=6666, frame_width=640, frame_protocol=self._session.get_video_protocol(),
                patterns_config="CLIENT_DATA/magic_patterns.txt", pattern_scale=0.13
            )
            self._stream_receiver = SurfaceReceiver(
                frame_port=self._session.get_video_sink_port(),
                tuio_port=self._session.get_tuio_sink_port(),
                server_ip=api_helper.SERVER_IP, ip=self._session.get_my_ip(),
                width=320, video_protocol=self._session.get_video_protocol()
            )
            # start streaming
            self._video_streamer.start()
            self._object_streamer.start()
            self._stream_receiver.start()
            # wait until streaming finished
            ret = self._object_streamer.wait()
            print("SurfaceStreams Object Streamer Process finished with exit code ", ret)
            ret = self._stream_receiver.wait()
            print("SurfaceStreams Stream Receiver Process finished with exit code ", ret)
        else:
            print("Server connection failed. Aborting.")

    def shutdown(self):
        if self._method == "webcam":
            self._shutdown_webcam_stream()
        elif self._method == "realsense":
            print("TODO realsense")
        else:
            raise ValueError("Method '" + self._method + "' not implemented.")

    def _shutdown_webcam_stream(self):
        if self._session.disconnect():
            print("### SUCCESS\n  > disconnected from server")
        else:
            print("### FAILURE\n  > could not disconnected from server")

        try:
            self._object_streamer.stop()
        except OSError:
            print("Object Streamer seems to be already closed.")

        try:
            self._stream_receiver.stop()
        except OSError:
            print("Receiver seems to be already closed.")

        try:
            self._video_streamer.stop()
        except OSError:
            print("Sender seems to be already closed.")

'''
def run_realsense_pipeline(send_port, realsense_dir, protocol="jpeg"):
    global VIDEO_STREAMER, STREAM_RECEIVER, SERVER_CONNECTION
    from processes.realsense_surface import RealsenseSurface
    from gstreamer.udp_video_receiver import UdpVideoReceiver
    from webutils import api_helper
    GObject.threads_init()
    Gst.init(None)
    
    SERVER_CONNECTION = ServerConnection(
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
'''