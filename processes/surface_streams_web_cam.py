from streaming.subprocess_sender import SubProcessWrapper


class WebCamSenderSubProcess(SubProcessWrapper):
    def __init__(self, server_port, my_port, server_ip="0.0.0.0", protocol="jpeg", server_stream_width=320, monitor=True):
        super().__init__()
        self._server_port = server_port
        self._my_port = my_port
        self._server_ip = server_ip
        self._protocol = protocol
        self._server_stream_width = server_stream_width
        self._monitor = monitor
        self._pipeline_description = ""
        self._compute_launch_command()

    def _compute_launch_command(self):
        gst_videoscale = "videoscale ! " \
                         "video/x-raw, width=" + str(self._server_stream_width) + ", " \
                         "pixel-aspect-ratio=1/1"

        gst_encoding = ""
        if self._protocol == "jpeg":
            gst_encoding += "jpegenc ! rtpgstpay"
        elif self._protocol == "vp8":
            gst_encoding += "vp8enc ! rtpvp8pay"
        elif self._protocol == "vp9":
            gst_encoding += "vp9enc ! rtpvp9pay"
        elif self._protocol == "mp4":
            gst_encoding += "avenc_mpeg4 ! rtpmp4vpay"
        elif self._protocol == "h264":
            gst_encoding += "avenc_h264 ! rtph264pay"
        elif self._protocol == "h265":
            gst_encoding += "avenc_h264 ! rtph265pay"

        self._pipeline_description += "v4l2src ! decodebin ! videoconvert ! "
        self._pipeline_description += "tee name=t ! queue ! "
        self._pipeline_description += gst_videoscale + " ! "
        self._pipeline_description += gst_encoding + " ! "
        self._pipeline_description += "udpsink port=" + str(self._server_port) + " host=" + str(self._server_ip) + "  "
        self._pipeline_description += "t. ! queue ! "
        self._pipeline_description += gst_encoding + " ! "
        self._pipeline_description += "udpsink port=" + str(self._my_port) + "  "
        if self._monitor:
            self._pipeline_description += "t. ! queue ! fpsdisplaysink"

        args = ["gst-launch-1.0"]
        for arg in self._pipeline_description.split(" "):
            args.append(arg)

        self._set_process_args(args)