import argparse
import time

from pythonosc import dispatcher
from pythonosc import osc_server
import multiprocessing


def _print_foo_handler(unused_addr, fixed_args, *lst):
    fixed_args[0].put([unused_addr, lst])


def _print_foo_handler_fixed(unused_addr, fixed_args, num, str, bool):
    fixed_args[0].put([unused_addr, num, str, bool])


def _print_foo_handler_mixed(unused_addr, fixed_args, num, *lst):
    fixed_args[0].put([unused_addr, num, lst])


def run(ip="127.0.0.1", port=5005):
    msg_queue = multiprocessing.Queue()

    osc_disp = dispatcher.Dispatcher()
    osc_disp.map("/foo", _print_foo_handler_mixed, msg_queue)

    server = osc_server.ThreadingOSCUDPServer((ip, port), osc_disp)
    print("Serving on {}".format(server.server_address))
    server_process = multiprocessing.Process(target=server.serve_forever)
    server_process.start()

    # this piece should be embedded into the frame by frame reconstruction on the client side
    while True:
        print("WAITING FOR MESSAGE")

        while not msg_queue.empty():
            print(msg_queue.get())

        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ip",
        default="127.0.0.1",
        help="The ip to listen on")

    parser.add_argument(
        "--port",
        type=int,
        default=5005,
        help="The port to listen on"
    )

    args = parser.parse_args()

    run(args.ip, args.port)
