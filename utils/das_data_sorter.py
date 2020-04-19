import pandas as pd 
import argparse 
from math import ceil

# accepts terminal commands
parser = argparse.ArgumentParser()
parser.add_argument("--file", help="Input CSV file", action="store", required=True)
parser.add_argument("--output", help="Returns the filtered data", default="filtered_data.csv", action="store")
parser.add_argument("--unit", help="Specify time units (seconds, s, or minutes, m)", default="seconds", 
                    choices=["seconds", "s", "minutes", "m"], action="store")
args = parser.parse_args()

# initialising data
data = pd.read_csv(args.file)

milliseconds = data["time"]
gps_course = data["gps_course"]
gps_speed = data["gps_speed"]
tempC = data["thermoC"]
tempF = data["thermoF"]
cadence = data["cadence"]
power = data["power"]
reed_vel = data["reed_velocity"]
reed_dis = data["reed_distance"]

time = []
if args.unit == "seconds" or args.unit == "s":
    time = milliseconds/1000
elif args.unit == "minutes" or args.unit =="m":
    time = milliseconds/1000/60

# sorts time into specific time unit
new_time = []
previous_time = 0
for i in range(len(time)):
    if time[i] > previous_time:
        # sets new previous_time, pushes current millisecond_indices into seconds array, creates new millisecond_indices
        # millisecond_indices is an array of indexes for milliseconds within the same specified unit
        if previous_time != 0:
            # ignores first iteration
            new_time.append(millisecond_indices)

        previous_time = ceil(time[i])
        millisecond_indices = []

    # pushes index into current millisecond_indices
    millisecond_indices.append(i)

new_time.append(millisecond_indices)

# averages data within the seconds, according to seconds array 
def avg_Data(array):
    avg_array = []

    for index_array in new_time:
        total = 0
        for index in index_array:
            total += array[index]

        avg = round(total/len(index_array), ndigits=2)
        avg_array.append(avg)
    return avg_array

# writes newly-manipulated data into new csv file
final = pd.DataFrame({
    "time": range(1, len(new_time)+1),
    "gps_course": avg_Data(gps_course),
    "gps_speed": avg_Data(gps_speed),
    "tempC": avg_Data(tempC),
    "tempF": avg_Data(tempF),
    "cadence": avg_Data(cadence),
    "power": avg_Data(power),
    "reed_velocity": avg_Data(reed_vel),
    "reed_distance": avg_Data(reed_dis)
})
final.to_csv(args.output, index=False)
