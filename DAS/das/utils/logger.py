from pathlib import Path
import paho.mqtt.client as mqtt
import csv
import time
import os
import asyncio
import logging
import re

CsvConfig = {
    "delimiter": ",",
    "quotechar": "`",
    "quoting": csv.QUOTE_ALL,
    "skipinitialspace": True,
    "fieldnames": ["time_delta", "mqtt_topic", "message"],
}

# Set logging to output all info by default (with a space for clarity)
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.WARNING)


class Recorder:
    """Record incoming MQTT messages on selected topics.

    Parameters
    ----------
    csv_folder_path : str
        Filepath of the folder where the logs are to be stored
    topics : List(str)
        A list containing the topic strings that are to be subscribed to
    broker_address : str
        The IP address that the MQTT broker lives on
    verbose : bool
        Specifies whether the incoming MQTT data and warnings are printed

    Attributes
    ----------
    TOPICS : List(str)
        List of topic names
    _recording : bool
        Whether the Recorder object is currently recording or not
    _START_TIME : `time`
        The current time used to produce time deltas
    _LOG_FILE : `File`
        Open log file object that can be written to
    _LOG_FILE_WRITER : `csv.DictWriter`
        Csv writter object that is used to write the data to the _LOG_FILE file
    _CLIENT : `paho.mqtt.client`
        MQTT client that connects to the broker and recives the messages
    """

    def __init__(
        self,
        csv_folder_path: str,
        topics: list = ["#"],
        broker_address: str = "localhost",
        verbose: bool = False,
    ) -> None:
        # The logger object can subscribe to many topics (if none are selected then it will subscribe to all)
        self.TOPICS = topics
        self._START_TIME = time.monotonic()

        # If set to verbose print info messages
        if verbose:
            logging.getLogger().setLevel(logging.INFO)

        # Create csv_folder_path folder if none exists
        Path(csv_folder_path).mkdir(parents=True, exist_ok=True)

        # Create the csv log and csv writter
        self._create_log_file(csv_folder_path)

        # Add headers for csv
        self._LOG_FILE_WRITER.writeheader()

        # Do not start logging when object is created (wait for start method)
        self._recording = False

        # Connect to MQTT broker
        self._CLIENT = mqtt.Client()
        self._CLIENT.on_connect = self._on_connect
        self._CLIENT.on_message = self._on_message
        self._CLIENT.connect(broker_address)
        self._CLIENT.loop_start()  # Threaded execution loop

    def _create_log_file(self, csv_folder_path: str) -> None:
        """Generates a log file ready to be written in.

        Parameters
        ----------
        csv_folder_path : str
            Filepath of the folder where the logs are to be stored
        """

        # Name the csv log file xxxx_log.csv where xxxx is a number
        previous_log_num = 0
        for filename in os.listdir(csv_folder_path):
            try:
                # Regular expression that extracts the decimal log number (group 1)
                current_log_num = int(re.search("(\d*)_log.csv", filename).group(1))
                if current_log_num > previous_log_num:
                    previous_log_num = current_log_num

            except AttributeError:
                logging.warning(f"{filename} should not be in {csv_folder_path}")

            except Exception as e:
                logging.error(f"{type(e)}: {e}")

        # Create the new log file and name it one more than the previous
        filename = f"{previous_log_num + 1}_log.csv"
        self._LOG_FILE = open(os.path.join(csv_folder_path, filename), "a")
        self._LOG_FILE_WRITER = csv.DictWriter(
            self._LOG_FILE,
            delimiter=CsvConfig["delimiter"],
            quotechar=CsvConfig["quotechar"],
            quoting=CsvConfig["quoting"],
            fieldnames=CsvConfig["fieldnames"],
        )

    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Callback function for MQTT broker on connection."""

        if rc == 0:
            logging.info("Connection Successful!")
        else:
            raise ConnectionError(
                "Connection was unsuccessful, check that the broker IP is corrrect"
            )

        # Subscribe to all of the topics
        try:
            for topic in self.TOPICS:
                self._CLIENT.subscribe(topic)
                logging.info(f"Subscribed to: {topic}")

        except Exception as e:
            logging.error(f"{type(e)}: {e}")

    def _on_message(self, client, userdata, msg) -> None:
        """Callback function for MQTT broker on message that logs the incoming MQTT message."""
        if self._recording:
            try:
                self.log(msg.topic, msg.payload.decode("utf-8"))

            except Exception as e:
                logging.error(f"{type(e)}: {e}")

    def log(self, mqtt_topic: str, message: str) -> None:
        """Logs the time delta and message data to self._LOG_FILE in the csv format.

        Parameters
        ----------
        mqtt_topic : str
            Incoming topic to be recorded
        message : str
            Corresponding message to be recorded
        """
        time_delta = time.monotonic() - self._START_TIME

        # Write data to csv file
        try:
            self._LOG_FILE_WRITER.writerow(
                {
                    "time_delta": time_delta,
                    "mqtt_topic": mqtt_topic,
                    "message": message,
                }
            )
            logging.info(f"{round(time_delta, 5): <10} | {mqtt_topic: <50} | {message}")

        except Exception as e:
            logging.error(f"{type(e)}: {e}")

    def start(self) -> None:
        """Starts the MQTT logging."""
        self._recording = True
        logging.info(f"Logging started!")

    def stop(self) -> None:
        """Graceful exit for closing the file and stopping the MQTT client."""
        self._recording = False
        self._CLIENT.loop_stop()
        self._LOG_FILE.close()
        logging.info(f"Data saved in {self._LOG_FILE.name}")


class Playback:
    """Playback MQTT messages from log files in realtime or faster.

    Parameters
    ----------
    filepath : str
        Filepath of the log file for playback
    broker_address : str
        The IP address that the MQTT broker lives on
    verbose : bool
        Specifies whether the outgoing MQTT data and warnings are printed

    Attributes
    ----------
    _BROKER_ADDRESS: bool
        The IP address of the MQTT broker
    _CLIENT : `paho.mqtt.client`
        MQTT client that connects to the broker and recives the messages
    _log_data: list(dict)
        A list of all of the rows in the log file stored in dict format
    """

    def __init__(
        self, filepath: str, broker_address: str = "localhost", verbose: bool = False
    ) -> None:

        # If set to verbose print info messages
        if verbose:
            logging.getLogger().setLevel(logging.INFO)

        # Read in data from log file and save each row in _log_data list
        log_file = open(filepath, "r")
        csv_reader = csv.DictReader(
            log_file,
            delimiter=CsvConfig["delimiter"],
            quotechar=CsvConfig["quotechar"],
            quoting=CsvConfig["quoting"],
            skipinitialspace=CsvConfig["skipinitialspace"],
        )

        self._log_data = []
        for row in csv_reader:
            # Convert time delta to float
            row["time_delta"] = float(row["time_delta"])
            self._log_data.append(row)

        # Connect to MQTT broker
        self._CLIENT = mqtt.Client()
        self._CLIENT.on_connect = self._on_connect
        self._CLIENT.connect(broker_address)

    def _on_connect(self, client, userdata, flags, rc) -> None:
        """Callback function for MQTT broker on connection."""

        if rc == 0:
            logging.info("Connection Successful!")
        else:
            raise ConnectionError(
                "Connection was unsuccessful, check that the broker IP is corrrect"
            )

    def play(self, speed: float = 1) -> None:
        """Play the logged data at a certain speed using an async function.

        Parameters
        ----------
        speed : float
            Speed multiplier to determine how fast to send out the data. A higher value means faster.
        """

        logging.info(f"⚡ Playback initiated at {speed}x speed ⚡")

        # Run the event loop to issue out all of the MQTT publishes
        asyncio.run(self._publish(speed))

    async def _publish(self, speed) -> None:
        """Async function that collects all the necessary publish functions and gathers them to then be run by the
        event loop.

        Parameters
        ----------
        speed : float
            Speed multiplier to determine how fast to send out the data. A higher value means faster.
        """

        async def _publish_aux(row):
            scaled_sleep = row["time_delta"] / speed
            await asyncio.sleep(scaled_sleep)

            logging.info(
                f"{round(row['time_delta'], 5): <10} | {round(scaled_sleep, 5): <10} | {row['mqtt_topic']: <50} | {row['message']}"
            )

            try:
                self._CLIENT.publish(row["mqtt_topic"], row["message"])

            except Exception as e:
                logging.error(f"{type(e)}: {e}")

        publish_queue = []
        for row in self._log_data:
            publish_queue.append(_publish_aux(row))

        # Load all async operation at the start using gather
        await asyncio.gather(*publish_queue, return_exceptions=True)
