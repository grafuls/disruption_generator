"""
Fake logger lets you populate a dummy log file. It will be filling it with
random gibberish for the time you specify. Once that time has passed, a target
log message will be added to dummy log file.
Target message means a line that you're looking for. This can be used for unit
testing or (mainly) for development purposes.
"""
import argparse
import pathlib
import string
import time


from random import choices, randint


""" Wishlist:
This is lazy implementation of this utility. If we find it useful, we might
want to:
- Provide a template for fake log messages (e.g. with timestamps)
- Let users define their own templates
- There's probably better solution than catching KeyboardInterrupt for
    indefinite running
- Display content of log file while running this script
"""


TARGET_MSG = "This one!"


def generate_random_string(target_msg, max_length=80):
    """
    Generate random string of letters and digits that is between 1 and
    max_length chars long.
    """
    random_str = target_msg
    while target_msg in random_str:  # Make sure target_msg in not included in generated string
        random_chars = choices(
            string.ascii_letters + string.digits, k=randint(1, max_length)
        )
        random_str = "".join(random_chars) + "\n"
    return random_str


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "-l",
        "--log-file",
        action="store",
        required=True,
        help="Path to the fake log file.",
    )
    parser.add_argument(
        "-a",
        "--append",
        action="store_true",
        default=False,
        help="If set to true and file specified in --log-fine already exists,"
        "new lines will be appened to end of the file.",
    )
    parser.add_argument(
        "-m",
        "--max-interval",
        action="store",
        default=1,
        type=int,
        help="How long should the interval between log messages be in seconds."
        "If used with --randomize, this will be the highest possible value"
        "of randomly generated number.",
    )
    parser.add_argument(
        "-r",
        "--randomize",
        action="store_true",
        default=False,
        help="If this is set to true, the number of seconds between log messages"
        "will be generated randomly with minimum value 0 and maximum value"
        "specified in --max-interval.",
    )
    parser.add_argument(
        "-t",
        "--target-msg",
        action="store",
        default=TARGET_MSG,
        help="Message that will be eventually sent to the log file once time "
        "specified in --seconds has passed.",
    )
    parser.add_argument(
        "-s",
        "--seconds",
        action="store",
        default=5,
        type=int,
        help="Target message will be sent to the log file in the next iteration"
        "after this many seconds have passed. If you set it to 0, target"
        "message will never be sent unless you interrput script execution"
        "by pressing Ctrl+C.",
    )

    args = parser.parse_args()

    log_file = pathlib.Path(args.log_file)

    with open(file=log_file, mode="a" if args.append else "w", buffering=1) as f:
        start_time = time.time()
        try:
            while True:
                f.write(generate_random_string(target_msg=args.target_msg))
                if args.randomize:
                    time_to_sleep = randint(0, 1000 * args.max_interval) / 1000
                else:
                    time_to_sleep = args.max_interval
                time.sleep(time_to_sleep)
                time_expired = args.seconds < time.time() - start_time
                if args.seconds != 0 and time_expired:
                    break
            f.write(args.target_msg + "\n")
        except KeyboardInterrupt:
            f.write(args.target_msg + "\n")


if __name__ == "__main__":
    main()
