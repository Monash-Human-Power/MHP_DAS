import sys
import argparse
import socket
from das.utils import logger

parser = argparse.ArgumentParser(
    description="MQTT playback",
    add_help=True,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument(
    "filepath", action="store", type=str, help="""Filepath of the csv log"""
)

parser.add_argument(
    "--host",
    action="store",
    type=str,
    default="localhost",
    help="""Address of the MQTT broker.""",
)

parser.add_argument(
    "-s",
    "--speed",
    action="store",
    type=float,
    default=1,
    help="""Playback speed up""",
)

parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    default=False,
    help="""Verbose logging output""",
)

if __name__ == "__main__":
    # Read command line arguments
    args = parser.parse_args()

    try:
        # Make logger object and initiate playback
        main_playback = logger.Playback(
            filepath=args.filepath, broker_address=args.host, verbose=args.verbose
        )

        main_playback.play(speed=args.speed)

    except KeyboardInterrupt:
        pass

    except socket.timeout as e:
        print(f"{type(e)}: {e}")
        print(f"The IP address of the MQTT broker is probably wrong")

    except Exception as e:
        print(f"{type(e)}: {e}")

    finally:
        # Graceful exit
        sys.exit()
