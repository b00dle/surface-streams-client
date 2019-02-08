import subprocess
import os
import signal

class SubProcessWrapper(object):
    """
    BC for all subprocess based senders.
    """

    def __init__(self):
        self._running = False
        self._subprocess = None
        self._process_args = []
        self.return_code = None

    def _set_process_args(self, args=[]):
        """
        Sets the subprocess.Popen(args) values for 'args'.
        args[0] determines the program to call, while remainder of list are
        optional cmd parameters. Call start(), to trigger subprocess instantiation.
        :param popen_list: list arguments in subprocess.Popen(args)
        :return:
        """
        if not self._running:
            self._process_args = args

    def cleanup(self):
        pass

    def start(self):
        """
        Starts subprocess with process_args set.
        See also: _set_process_args, stop
        :return: process ID
        """
        if self._running or len(self._process_args) == 0:
            return
        cmd_str = ""
        for arg in self._process_args:
            cmd_str += " " + arg
        print("Running:", cmd_str)
        self._subprocess = subprocess.Popen(self._process_args)
        print("  > PID", self._subprocess.pid)
        self._running = True
        return self._subprocess.pid

    def stop(self):
        """
        Stops the subprocess if running.
        See also: _set_process_args, start
        :return:
        """
        if not self._running:
            return
        self._subprocess.terminate()
        self.return_code = self._subprocess.wait()
        self._running = False

    def is_running(self):
        return self._running

    def wait(self):
        return self._subprocess.wait()

    def join(self):
        self._subprocess.join()


class RealsenseSender(SubProcessWrapper):
    """
    Class used to encapsulate execution of Realsense SurfaceStreams reconstruction
    and streaming data over udp channel.
    """

    def __init__(self, realsense_dir="./", protocol="jpeg"):
        """
        Constructor.
        :param realsense_dir: directory where ./realsense executable can be found.
        Program can be found and built at https://github.com/floe/surface-streams
        :param protocol: encoding for udp stream. Choose 'jpeg', 'vp8', 'mp4' or 'h264'
        """
        self._protocol = protocol
        self._realsense_dir = realsense_dir
        self._host = "0.0.0.0"
        self._port = 5000
        super().__init__()

    def _compute_launch_command(self):
        """
        Creates the subprocess creation call for realsense executable.
        Includes a GStreamer pipeline for streaming reconstruction over udp.
        :return:
        """
        gst_launch_cmd = ""
        if self._protocol == "jpeg":
            gst_launch_cmd = "videoconvert ! tee name=t ! queue ! jpegenc ! rtpgstpay ! "
        elif self._protocol == "vp8":
            gst_launch_cmd = "videoconvert ! tee name=t ! queue ! vp8enc ! rtpvp8pay ! "
        elif self._protocol == "vp9":
            gst_launch_cmd = "videoconvert ! tee name=t ! queue ! vp9enc ! rtpvp9pay ! "
        elif self._protocol == "mp4":
            gst_launch_cmd = "videoconvert ! tee name=t ! queue ! avenc_mpeg4 ! rtpmp4vpay ! "
        elif self._protocol == "h264":
            gst_launch_cmd = "videoconvert ! tee name=t ! queue ! x264enc tune=zerolatency ! rtph264pay ! "
        elif self._protocol == "h265":
            gst_launch_cmd = "videoconvert ! tee name=t ! queue ! x265enc tune=zerolatency ! rtph265pay ! "
        gst_launch_cmd += "udpsink host=" + self._host + " port=" + str(self._port) + " "
        gst_launch_cmd += "t. ! queue ! fpsdisplaysink"
        gst_launch_cmd = '"' + gst_launch_cmd + ' "'
        args = []
        args.append(self._realsense_dir+"realsense")
        args.append("!")
        args.append(gst_launch_cmd)
        self._set_process_args(args)

    def set_host(self, host):
        """
        Sets host receiving SurfaceStreams realsense stream.
        :param host: host ip of format XXX.XXX.XXX.XXX, default = 0.0.0.0
        :return:
        """
        self._host = host
        self._compute_launch_command()

    def set_port(self, port):
        """
        Sets host port receiving SurfaceStreams realsense stream.
        :param port: port number, default = 5000
        :return:
        """
        self._port = port
        self._compute_launch_command()