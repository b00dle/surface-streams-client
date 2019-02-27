from datetime import datetime
from processes.surface_receiver import SurfaceReceiver
from processes.surface_tracker import SurfaceTracker
from processes.webcam_surface import WebcamSurface
from processes.executable_gst_surface import ExecutableGstSurface
from webutils.surface_streams_session import SurfaceStreamsSession
from webutils import api_helper


def create_timestamp():
    return datetime.now().strftime(("%Y-%m-%d %H:%M:%S"))


class SurfaceStreamsClient(object):
    _available_methods = ["webcam", "gstexec"]

    def __init__(self, my_ip="0.0.0.0", server_ip="0.0.0.0", video_send_port=5002, method="webcam",
                 executable_path="./realsense", video_protocol="jpeg",
                 patterns_config="CLIENT_DATA/tracking_patterns.txt",
                 surface_port=6666, pre_gst_args=["!"]):
        api_helper.SERVER_IP = server_ip
        self._method = method
        self._executable_path = executable_path
        self._pre_gst_args = pre_gst_args
        self._patterns_config = patterns_config
        self._surface_port = surface_port
        self._session = SurfaceStreamsSession(
            my_ip=my_ip, name="python-client-" + create_timestamp(),
            video_src_port=video_send_port, video_protocol=video_protocol
        )
        # will be filled upon run (depending on set method)
        self._stream_receiver = None
        self._video_streamer = None
        self._object_streamer = None

    def run(self):
        if self._method == "webcam":
            self._run_webcam_stream()
        elif self._method == "gstexec":
            self._run_gstexec_stream()
        else:
            raise ValueError("Method '" + self._method + "' not implemented.")
        self.shutdown()

    def _run_webcam_stream(self):
        # connect to surface streams server
        if self._session.connect():
            # initialize video streamer, object streamer and stream receiver
            self._video_streamer = WebcamSurface(
                server_port=self._session.get_video_src_port(), my_port=self._surface_port,
                server_ip=api_helper.SERVER_IP, protocol=self._session.get_video_protocol(),
                monitor=False
            )
            self._object_streamer = SurfaceTracker(
                server_ip=api_helper.SERVER_IP, server_tuio_port=5001,
                frame_port=self._surface_port, frame_width=640, frame_protocol=self._session.get_video_protocol(),
                patterns_config=self._patterns_config, pattern_scale=0.13
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
            print("Server co nnection failed. Aborting.")

    def _run_gstexec_stream(self):
        # connect to surface streams server
        if self._session.connect():
            # initialize video streamer, object streamer and stream receiver
            self._video_streamer = ExecutableGstSurface(
                server_port=self._session.get_video_src_port(), server_ip=api_helper.SERVER_IP,
                my_port=self._surface_port, executable_path=self._executable_path, protocol=self._session.get_video_protocol(),
                monitor=True, server_stream_width=640, pre_gst_args=self._pre_gst_args
            )
            self._object_streamer = SurfaceTracker(
                server_ip=api_helper.SERVER_IP, server_tuio_port=5001,
                frame_port=self._surface_port, frame_width=640, frame_protocol=self._session.get_video_protocol(),
                patterns_config=self._patterns_config, pattern_scale=0.6
            )
            self._stream_receiver = SurfaceReceiver(
                frame_port=self._session.get_video_sink_port(),
                tuio_port=self._session.get_tuio_sink_port(),
                server_ip=api_helper.SERVER_IP, ip=self._session.get_my_ip(),
                width=720, video_protocol=self._session.get_video_protocol()
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
        if self._method in self._available_methods:
            self._shutdown_surface_stream()
        else:
            raise ValueError("Method '" + self._method + "' not implemented.")

    def _shutdown_surface_stream(self):
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