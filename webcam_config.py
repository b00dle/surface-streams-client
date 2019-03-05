if __name__ == "__main__":
    import sys
    from subprocess import call

    config = {
        "brightness": 128,
        "contrast": 50,
        "saturation": 170,
        "white_balance_temperature_auto": 1,
        "gain": 192,
        "power_line_frequency": 2,
        "white_balance_temperature": 3070,
        "sharpness": 40,
        "backlight_compensation": 0,
        "exposure_auto": 3,
        "exposure_auto_priority": 1
    }

    device = "/dev/video0"

    if len(sys.argv) > 1:
        arg_i = 1
        while arg_i < len(sys.argv):
            arg = sys.argv[arg_i]
            if arg == "-device":
                arg_i += 1
                device = sys.argv[arg_i]
            arg_i += 1

    for key, value in config.items():
        call(["v4l2-ctl", "-c", key + "=" + str(value), "-d", device])