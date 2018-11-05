import os
import gi
gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, Gtk, GstVideo, GdkX11
from streaming.gst_pipeline import GstPipeline
from pprint import pprint

class UdpVideoReceiver(GstPipeline):
    '''
    Implements a GST pipeline to receive jpeg encoded rtp-gst frames over udp,
    decode them, convert them to video and produce output into
    an embedded gtksink window.

    gst pipeline description:
    gst-launch-1.0 udpsrc port=5000 ! application/x-rtp, media=application ! queue !
        rtpgstdepay ! jpegdec ! videoconvert ! gtksink
    '''

    def __init__(self):
        super().__init__("Udp-Video-Receiver")
        self._init_ui()
        self._init_gst_pipe()

    def _init_ui(self):
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_title("Udp Video Receiver")
        self.window.set_default_size(500, 400)
        self.window.connect("destroy", Gtk.main_quit, "WM destroy")
        self.vbox_layout = Gtk.VBox()
        self.window.add(self.vbox_layout)
        self.window.show_all()

    def _init_gst_pipe(self):
        # create necessary elements
        self.udp_src = self.make_add_element("udpsrc", "udpsrc")
        self.udp_src.set_property("caps", Gst.caps_from_string("application/x-rtp, media=(string)application, clock-rate=(int)90000, encoding-name=(string)X-GST, caps=(string)aW1hZ2UvanBlZywgc29mLW1hcmtlcj0oaW50KTAsIHdpZHRoPShpbnQpMTI4MCwgaGVpZ2h0PShpbnQpNzIwLCBwaXhlbC1hc3BlY3QtcmF0aW89KGZyYWN0aW9uKTEvMSwgZnJhbWVyYXRlPShmcmFjdGlvbikyNDAwMC8xMDAx, capsversion=(string)0, payload=(int)96, ssrc=(uint)2277765570, timestamp-offset=(uint)3095164038, seqnum-offset=(uint)16152"))
        self.src_queue = self.make_add_element("queue", "src_queue")
        self.rtp_depay = self.make_add_element("rtpgstdepay", "rtp_depay")
        self.jpeg_decoder = self.make_add_element("jpegdec", "jpeg_decoder")
        self.videoconvert = self.make_add_element("videoconvert", "video_converter")
        self.videosink = self.make_add_element("gtksink", "videosink")
        self.vbox_layout.add(self.videosink.props.widget)
        self.videosink.props.widget.show()

        self.link_elements(self.udp_src, self.src_queue)
        self.link_elements(self.src_queue, self.rtp_depay)
        self.link_elements(self.rtp_depay, self.jpeg_decoder)
        self.link_elements(self.jpeg_decoder, self.videoconvert)
        self.link_elements(self.videoconvert, self.videosink)

    #def start(self, port):
    #    self.udp_src.set_property("port", port)
    #    self.pipeline.set_state(Gst.State.PLAYING)

    def start(self, port):
        self.udp_src.set_property("port", port)
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_udp_bus_message(self, bus, message):
        print("### on_udp_bus_message")
        print("  > message.src", message.src.get_name())

    def on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.STREAM_START:
            print("stream start")
            #self.pipeline.set_state(Gst.State.PLAYING)
        elif t == Gst.MessageType.ERROR:
            self.pipeline.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print(message.src.get_name()+" Error: %s" % err, debug)
        elif t == Gst.MessageType.STATE_CHANGED:
            old_state, new_state, pending_state = message.parse_state_changed()
            print(message.src.get_name()+" state changed from %s to %s." %
                  (old_state.value_nick, new_state.value_nick))
        elif t == Gst.MessageType.ELEMENT:
            msg_src = message.src.get_name()
            if "udp" in msg_src:
                pprint(dir(message.src))
                print(msg_src)
        elif t == Gst.MessageType.EOS:
            print("reached end")
        elif t == Gst.MessageType.WARNING:
            wrn, debug = message.parse_warning()
            print(message.src.get_name() + " Warning: %s" % wrn, debug)
        else:
            print(t)


class UdpVideoReceiverAlt(GstPipeline):
    '''
    Implements a GST pipeline to receive h263 encoded rtp-video frames over udp,
    decode them, convert them to video and produce output into
    an autovideosink window.

    gst pipeline description:
    gst-launch-1.0 udpsrc port=5000 ! application/x-rtp, media=video ! queue !
        rtph263pdepay ! avdec_h263 ! autovideosink
    '''

    def __init__(self):
        super().__init__("Udp-Video-Receiver")
        self._init_ui()
        self._init_gst_pipe()

    def _init_ui(self):
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_title("Udp Video Receiver")
        self.window.set_default_size(500, 400)
        self.window.connect("destroy", Gtk.main_quit, "WM destroy")
        self.vbox_layout = Gtk.VBox()
        self.window.add(self.vbox_layout)
        self.movie_window = Gtk.DrawingArea()
        self.vbox_layout.add(self.movie_window)
        self.window.show_all()

    def _init_gst_pipe(self):
        # create necessary elements
        self.udp_src = self.make_add_element("udpsrc", "udpsrc")
        self.udp_src.set_property("port", 5000)
        self.udp_src.set_property("caps", Gst.caps_from_string("application/x-rtp, media=video"))
        self.src_queue = self.make_add_element("queue", "src_queue")
        self.rtp_depay = self.make_add_element("rtph263pdepay", "rtp_depay")
        self.av_decoder = self.make_add_element("avdec_h263", "av_decoder")
        self.videosink = self.make_add_element("autovideosink", "videosink")

        self.link_elements(self.udp_src, self.src_queue)
        self.link_elements(self.src_queue, self.rtp_depay)
        self.link_elements(self.rtp_depay, self.av_decoder)
        self.link_elements(self.av_decoder, self.videosink)

        self.pipeline.set_state(Gst.State.PLAYING)

    def on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.STREAM_START:
            print("stream start")
            self.pipeline.set_state(Gst.State.PLAYING)
        elif t == Gst.MessageType.ERROR:
            self.pipeline.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print(message.src.get_name()+" Error: %s" % err, debug)
        elif t == Gst.MessageType.STATE_CHANGED:
            old_state, new_state, pending_state = message.parse_state_changed()
            print(message.src.get_name()+" state changed from %s to %s." %
                  (old_state.value_nick, new_state.value_nick))
        elif t == Gst.MessageType.ELEMENT:
            pass
        else:
            pass

    def on_bus_sync_message(self, bus, message):
        """ Sets x window ID once image sink is ready to prepare output. """
        message_name = message.get_structure().get_name()
        if message_name == "prepare-window-handle":
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_window_handle(self.movie_window.get_property("window").get_xid())


class UdpVideoReceiverAlt2(GstPipeline):
    '''
    Implements a GST pipeline to receive jpeg encoded rtp-gst frames over udp,
    decode them, convert them to video and produce output into
    an autovideosink window.

    gst pipeline description:
    gst-launch-1.0 udpsrc port=5000 ! application/x-rtp, media=application ! queue !
        rtpgstdepay ! jpegdec ! autovideosink
    '''

    # works, but doesn't put video frame into xwindow
    def __init__(self):
        super().__init__("Udp-Video-Receiver")
        self._init_ui()
        self._init_gst_pipe()

    def _init_ui(self):
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.set_title("Udp Video Receiver")
        self.window.set_default_size(500, 400)
        self.window.connect("destroy", Gtk.main_quit, "WM destroy")
        self.vbox_layout = Gtk.VBox()
        self.window.add(self.vbox_layout)
        self.movie_window = Gtk.DrawingArea()
        self.vbox_layout.add(self.movie_window)
        self.window.show_all()

    def _init_gst_pipe(self):
        # create necessary elements
        self.udp_src = self.make_add_element("udpsrc", "udpsrc")
        self.udp_src.set_property("port", 5000)
        self.udp_src.set_property("caps", Gst.caps_from_string("application/x-rtp, media=application"))
        self.src_queue = self.make_add_element("queue", "src_queue")
        self.rtp_depay = self.make_add_element("rtpgstdepay", "rtp_depay")
        self.jpeg_decoder = self.make_add_element("jpegdec", "jpeg_decoder")
        self.videosink = self.make_add_element("autovideosink", "videosink")

        self.link_elements(self.udp_src, self.src_queue)
        self.link_elements(self.src_queue, self.rtp_depay)
        self.link_elements(self.rtp_depay, self.jpeg_decoder)
        self.link_elements(self.jpeg_decoder, self.videosink)

        self.pipeline.set_state(Gst.State.PLAYING)

    def on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.STREAM_START:
            print("stream start")
            self.pipeline.set_state(Gst.State.PLAYING)
        elif t == Gst.MessageType.ERROR:
            self.pipeline.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print(message.src.get_name()+" Error: %s" % err, debug)
        elif t == Gst.MessageType.STATE_CHANGED:
            old_state, new_state, pending_state = message.parse_state_changed()
            print(message.src.get_name()+" state changed from %s to %s." %
                  (old_state.value_nick, new_state.value_nick))
        elif t == Gst.MessageType.ELEMENT:
            pass
        else:
            pass

    def on_bus_sync_message(self, bus, message):
        """ Sets x window ID once image sink is ready to prepare output. """
        message_name = message.get_structure().get_name()
        #if message_name == "prepare-window-handle":
        #    imagesink = message.src
        #    imagesink.set_property("force-aspect-ratio", True)
        #    imagesink.set_window_handle(self.movie_window.get_property("window").get_xid())