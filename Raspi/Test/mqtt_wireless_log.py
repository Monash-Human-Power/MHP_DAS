import argparse
import paho.mqtt.client as mqtt
import os
import pandas as pd
from DataToTempCSV import DataToTempCSV
import json


def on_connect(client, userdata, flags, rc):
    remove_temps(find_temp_csvs())  # Remove old temp files

    if rc == 0:
        print("Connected Successfully! Result code: " + str(rc))

    else:
        print("Something went wrong! Result code: " + str(rc))

    subscribe_to_all(client)


def subscribe_to_all(client):
    # Subscribe to all of the data topics
    client.subscribe("/v3/wireless-module/1/data")
    client.subscribe("/v3/wireless-module/2/data")
    client.subscribe("/v3/wireless-module/3/data")

    # Subscribe to all of the battery topics
    client.subscribe("/v3/wireless-module/battery/low")
    client.subscribe("/v3/wireless-module/1/battery")
    client.subscribe("/v3/wireless-module/2/battery")
    client.subscribe("/v3/wireless-module/3/battery")

    # Subscribe to all of the start topics
    client.subscribe("/v3/wireless-module/1/start")
    client.subscribe("/v3/wireless-module/2/start")
    client.subscribe("/v3/wireless-module/3/start")

    # Subscribe to all of the stop topics
    client.subscribe("/v3/wireless-module/1/stop")
    client.subscribe("/v3/wireless-module/2/stop")
    client.subscribe("/v3/wireless-module/3/stop")


def on_message(client, userdata, msg):
    module_id = str("M" + msg.topic[20])
    if msg.topic.endswith("start"):
        # Decode the data as utf-8 and load into python dict
        start_data = msg.payload.decode("utf-8")
        start_data = json.loads(start_data)

        # Update is_recording dict with correct filename and status
        is_recording[module_id] = True
        is_recording[module_id + "_filename"] = start_data["filename"]
        print(module_id, "STARTED")

    elif msg.topic.endswith("stop"):
        # Update is_recording to stop the recording of the wireless module
        is_recording[module_id] = False
        print(module_id, "STOPPED")

        # Save the temporary data into a perminent CSV
        save_temp_csv(module_id)

    else:
        # low battery
        if msg.topic == "/v3/wireless-module/battery/low":
            DataToTempCSV(msg)
        # low battery just record normal data
        elif is_recording[module_id] is True:
            DataToTempCSV(msg, module_id)


def save_temp_csv(module_id):
    output_filename = is_recording[module_id + "_filename"]
    temp_filepaths = find_temp_csvs(module_id)
    merge_temps(output_filename, temp_filepaths)
    remove_temps(temp_filepaths)


def find_temp_csvs(module_id=""):
    """Searches throught the current directory and finds all the temp files and
    merges them it finds a """
    current_dir = os.path.dirname(__file__)

    if current_dir == '':
        filepaths = os.listdir()
    else:
        filepaths = os.listdir(current_dir)

    temp_filepaths = []
    for filename in filepaths:
        # Find the temp filepaths and store in the array
        if filename.startswith(".~temp_" + module_id) and filename.endswith(".csv"):
            if current_dir == '':
                temp_filepaths.append(filename)
            else:
                temp_filepaths.append(current_dir + '/' + filename)

    return temp_filepaths


def remove_temps(filepaths):
    """ Removes the files in the list of filepaths """
    for file in filepaths:
        os.remove(file)


def merge_temps(output_filename, temp_filepaths):
    temps_dataframes = []
    for temp_filename in temp_filepaths:
        temp_df = pd.read_csv(temp_filename)
        temps_dataframes.append(temp_df)

    merged_dataframe = pd.concat(temps_dataframes, axis=1)

    merged_dataframe.to_csv(output_filename)


if __name__ == "__main__":
    is_recording = {
        "M1": False,
        "M2": False,
        "M3": False,
        "M1_filename": None,
        "M2_filename": None,
        "M3_filename": None,
    }

    broker_address = 'localhost'
    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker_address)

    client.loop_forever()
