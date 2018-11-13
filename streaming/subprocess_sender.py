import subprocess


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

    def start(self):
        """
        Starts subprocess with process_args set.
        See also: _set_process_args, stop
        :return:
        """
        if self._running or len(self._process_args) == 0:
            return
        self._subprocess = subprocess.Popen(self._process_args)
        self._running = True

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


class RealsenseSender(SubProcessWrapper):
    def __init__(self, realsense_dir="./"):
        super().__init__()
        self._realsense_dir = realsense_dir
        self._host = "0.0.0.0"
        self._port = 5000

    def _compute_launch_command(self):
        self._set_process_args([
            self._realsense_dir+"realsense",
            "!",
            "\"videoconvert ! jpegenc ! rtpgstpay ! "
            "udpsink host=" + self._host + " port=" + self._port + "\""
        ])

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