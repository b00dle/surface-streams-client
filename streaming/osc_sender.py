import argparse
import time

from pythonosc import udp_client


def run(ip="127.0.0.1", port=5005):
    client = udp_client.SimpleUDPClient(ip, port)

    for x in range(10):
        client.send_message("/foo", [x, "yo", True])
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ip",
        default="127.0.0.1",
        help="The ip of the OSC server"
    )

    parser.add_argument(
        "--port", type=int, default=5005,
        help="The port the OSC server is listening on")

    args = parser.parse_args()

    run(args.ip, args.port)
