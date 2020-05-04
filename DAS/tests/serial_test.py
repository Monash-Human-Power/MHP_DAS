import argparse
import os
import platform
import paho.mqtt.client as mqtt

from das_data_generator import send_csv_data, send_fake_data

# Arguments
parser = argparse.ArgumentParser(description='DAS serial test script', add_help=True)
parser.add_argument('-t', '--time', action='store', type=int, default=1, help="length of time to send data")
parser.add_argument('-r', '--rate', action='store', type=float, default=0.5, help="rate of data in seconds")
parser.add_argument('--host', action='store', type=str, default="localhost", help="address of the MQTT broker")
parser.add_argument('-f', '--file', action='store', type=str, help="The csv file to replay. If not specified, makes up data.")
parser.add_argument('-j', '--jump', action='store', type=int, default=0, help="Starts replaying from a specified time (in seconds)")

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))

def run(args):
    # Check that we are running on Linux.
    # os.openpty and os.ttyname are only available on unix (NOT windows)
    # Additionally, unexpected behaviour seems to occur on Mac (see PR #28)
    if platform.system() != "Linux":
        raise Exception("Serial test only works on Linux. If you are on Windows, perhaps try using WSL.")

    # Create pseudo-terminal pair
    master, slave = os.openpty()

    # Show ports
    print("Master serial port:", os.ttyname(master))
    print("Slave serial port (for DAS.js):", os.ttyname(slave))

    # Allow user to start DAS.js before starting so that it recieves the 'start' topic
    input("Run 'node DAS.js -p {}' then press enter".format(os.ttyname(slave)))

    # Connect to MQTT
    broker_address = args.host
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(broker_address)
    # Publish to filename topic so DAS.js starts rebroadcasting stuff
    client.publish("filename", "serial_test")

    # Function to write the data to serial
    send_data_func = lambda data: os.write(master, (data + "\n").encode())

    send_data_func("start")

    if args.file is None:
        send_fake_data(send_data_func, args.time, args.rate, immitate_teensy=True)
    else:
        send_csv_data(send_data_func, args.file, args.jump, immitate_teensy=True)

    send_data_func("stop")

parser_args = parser.parse_args()
run(parser_args)