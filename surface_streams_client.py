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
    _available_inputs = ["webcam", "gstexec"]

    def __init__(self, my_ip="0.0.0.0", server_ip="0.0.0.0", video_send_port=5002, input="webcam",
                 executable_path="./realsense", video_protocol="jpeg", mixing_mode="other",
                 patterns_config="CLIENT_DATA/tracking_patterns.txt",
                 surface_port=6666, pre_gst_args=["!"], webcam_device="/dev/video0",
                 tracking_mode="local", tracking_ip="0.0.0.0"):
        api_helper.SERVER_IP = server_ip
        self._input = input
        self._executable_path = executable_path
        self._pre_gst_args = pre_gst_args
        self._webcam_device = webcam_device
        self._patterns_config = patterns_config
        self._surface_port = surface_port
        self._tracking_mode = tracking_mode
        self._tracking_ip = tracking_ip
        self._session = SurfaceStreamsSession(
            my_ip=my_ip, name="python-client-" + create_timestamp(),
            video_src_port=video_send_port, video_protocol=video_protocol,
            mixing_mode=mixing_mode
        )
        # will be filled upon run (depending on set method)
        self._stream_receiver = None
        self._video_streamer = None
        self._object_streamer = None

    def run(self):
        if self._input not in self._available_inputs:
            raise ValueError("Method '" + self._input + "' not implemented.")
        # connect to surface streams server
        if self._session.connect():
            # setup input device surface (delivers capture data)
            self._init_surface_input()
            # setup tracking of data received by input device (evaluates capture data)
            self._init_surface_tracking()
            # setup receiving of merged video & tracking data from server (produces output frame)
            self._init_surface_receiving()
            # start streaming (blocks until tracking & receiving done)
            self._run_streaming()
            # shutdown once finished
            self.shutdown()
        else:
            print("Server connection failed. Aborting.")

    def _init_surface_input(self):
        if self._input not in SurfaceStreamsClient._available_inputs:
            raise ValueError("Input '" + self._input + "' not implemented.")

        my_ip = "0.0.0.0"
        if self._tracking_mode == "remote":
            my_ip = self._tracking_ip

        if self._input == "webcam":
            self._video_streamer = WebcamSurface(
                server_port=self._session.get_video_src_port(), my_port=self._surface_port,
                server_ip=api_helper.SERVER_IP, my_ip=my_ip,
                protocol=self._session.get_video_protocol(),
                monitor=False, device=self._webcam_device
            )
        elif self._input == "gstexec":
            self._video_streamer = ExecutableGstSurface(
                server_port=self._session.get_video_src_port(), server_ip=api_helper.SERVER_IP,
                my_port=self._surface_port, my_ip=my_ip,
                executable_path=self._executable_path,
                protocol=self._session.get_video_protocol(),
                monitor=True, server_stream_width=640, pre_gst_args=self._pre_gst_args
            )

    def _init_surface_tracking(self):
        if self._tracking_mode == "local":
            self._object_streamer = SurfaceTracker(
                server_ip=api_helper.SERVER_IP, server_tuio_port=5001,
                frame_port=self._surface_port, frame_width=640, frame_protocol=self._session.get_video_protocol(),
                patterns_config=self._patterns_config, pattern_scale=0.13,
                user_id=self._session.get_id()
            )
        elif self._tracking_mode == "remote":
            pass

    def _init_surface_receiving(self):
        self._stream_receiver = SurfaceReceiver(
            frame_port=self._session.get_video_sink_port(),
            tuio_port=self._session.get_tuio_sink_port(),
            server_ip=api_helper.SERVER_IP, ip=self._session.get_my_ip(),
            width=320, video_protocol=self._session.get_video_protocol(),
            user_id=self._session.get_id()
        )

    def _run_streaming(self):
        self._video_streamer.start()
        self._stream_receiver.start()
        if self._object_streamer is not None:
            self._object_streamer.start()
            # wait until object streaming finished
            ret = self._object_streamer.wait()
            print("SurfaceStreams Object Streamer Process finished with exit code ", ret)
        # wait until stream receiving streaming finished
        ret = self._stream_receiver.wait()
        print("SurfaceStreams Stream Receiver Process finished with exit code ", ret)

    def shutdown(self):
        if self._input not in self._available_inputs:
            raise ValueError("Method '" + self._input + "' not implemented.")

        if self._session.disconnect():
            print("### SUCCESS\n  > disconnected from server")
        else:
            print("### FAILURE\n  > could not disconnected from server")

        try:
            if self._object_streamer is not None:
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