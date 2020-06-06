import pandas as pd 
from argparse import ArgumentParser
from numpy import ceil, median

# accepts terminal arguments
parser = ArgumentParser()
parser.add_argument("--input", help="Reads the inputted CSV file to filter", action="store", required=True)
parser.add_argument("--output", help="Writes the filtered data onto a new CSV file under this name", action="store", required=True)
parser.add_argument("--unit", help="Specify time units [seconds, s, or minutes, m]. Default is in seconds.", default="seconds", 
                    choices=["seconds", "s", "minutes", "m"], action="store")
parser.add_argument("--smooth", help="Smooths data points using 3-point mean or median smoothing", choices=["mean", "median"], action="store")
args = parser.parse_args()

class DasSort:
    def __init__(self, file_input:pd.DataFrame, unit:str) -> None:
        self.indexes = None
        self.time = self.convert_time(file_input["time"], unit)
        self.gps = self.gps_data(file_input["gps"])
        self.gps_lat = self.average_data(file_input["gps_lat"])
        self.gps_long = self.average_data(file_input["gps_long"])
        self.gps_alt = self.average_data(file_input["gps_long"])
        self.gps_course = self.average_data(file_input["gps_course"])
        self.gps_speed = self.average_data(file_input["gps_speed"])
        self.gps_satellites = self.average_data(file_input["gps_satellites"])
        self.ax = self.average_data(file_input["aX"])
        self.ay = self.average_data(file_input["aY"])
        self.az = self.average_data(file_input["aZ"])
        self.gx = self.average_data(file_input["gX"])
        self.gy = self.average_data(file_input["gY"])
        self.gz = self.average_data(file_input["gZ"])
        self.thermoc = self.average_data(file_input["thermoC"])
        self.thermof = self.average_data(file_input["thermoF"])
        self.pot = self.average_data(file_input["pot"])
        self.cadence = self.average_data(file_input["cadence"])
        self.power = self.average_data(file_input["power"])
        self.reed_velocity = self.average_data(file_input["reed_velocity"])
        self.reed_distance = self.average_data(file_input["reed_distance"])

    def convert_time(self, milliseconds:pd.Series, unit) -> pd.Series:
        '''Returns the conversion of the time data points from milliseconds to the specified time unit, depending on the 
        argument passed by unit.
        
        unit accepts only seconds/s and minutes/m as arguments. 
        '''
        if unit == "seconds" or unit == "s":
            new_time = milliseconds/1000
        elif unit == "minutes" or unit == "m":
            new_time = milliseconds/1000/60
        else:
            raise ValueError("Argument only accepts either seconds/s or minutes/m")
        
        # sets the groups of indexes to use for averaging in future
        self.indexes = self.group_index(new_time)

        return range(1,len(self.indexes)+1)

    def group_index(self, time:pd.Series) -> pd.Series:
        '''Returns a universal array of arrays of indexes, based on the specified time unit. Each array represents the indexes 
        of the data points within the same time interval. (eg. 1123ms and 1748ms are in the same time interval for seconds, 
        but 2453ms isn't)

        When given a valid value for args.unit, function will group the indexes within the same time interval in an array.
        Once all the indexes of a time interval has been accounted for, the array of indexes will be pushed into a
        universal array so that each element represents the data points of one singular time interval.
        '''
        universal_array = []
        index_array = []
        previous_time = 0

        for i in range(len(time)):
            if time[i] > previous_time:
                # if true, then time at time[i] is the next second/minute
                if previous_time != 0:
                    # appends index array into universal array, but ignores the first iteration
                    universal_array.append(index_array)

                previous_time = ceil(time[i])
                index_array = [] # recreates new array if previous time has changed
            index_array.append(i) 
        universal_array.append(index_array) # pushes the final array

        return universal_array

    def mean(self, data_array:pd.Series) -> float:
        '''Finds the average of a given set of numbers. 

        Disregards None and zero in calculation. Otherwise, if input is invalid, then raises error.
        '''
        total = 0
        length = len(data_array)

        for number in data_array:
            if number > 0 or number < 0:
                # 'number' value is valid
                total += number
            elif number == 0 or pd.isna(number):
                # None and zeroes are ignored
                length -= 1
                continue
            else:
                # 'number' value is invalid
                raise ValueError("Data point invalid and is neither zero nor None. The data point was "+str(number)+". ("+str(type(number))+")")
        try:
            return total/length
        except ZeroDivisionError:
            # in the event where length = 0, due to all the elements in data_array being ignored
            return 0 

    def average_data(self, data:pd.Series) -> pd.Series:
        '''Returns a column of new data points that has been averaged, based on specified time unit. 

        Finds the average of all data points within the same time interval. Appends this new value into an array, then continues
        to the next time interval. Once all time intervals have been accounted for, returns the set of new data points.
        '''
        average_data_array = []

        for index_array in self.indexes:
            current_average = self.mean(data[index_array])
            current_average = round(current_average, ndigits=2)
            average_data_array.append(current_average)

        return average_data_array
    
    def gps_data(self, data:pd.Series) -> pd.Series:
        '''Returns the data array of the time intervals which the GPS was turned on. 
        
        0 for when GPS was turned off, 1 for when turned on.
        '''
        new_gps_data = []

        for index_array in self.indexes:
            if 1 in data[index_array].values:
                new_gps_data.append(1)
            else:
                new_gps_data.append(0)

        return new_gps_data
    
    def smooths_data(self, data:pd.Series, technique:str, n:int=3) -> pd.Series:
        if n < 3 or n > len(data):
            raise ValueError("Number of smoothing points must be at least 3 and less than the length of the data set to perform smoothing.")
        smooth_data_array = [] 

        if technique == "mean" and n % 2 != 0: # Mean Smoothing for odd number N
            for i in range(len(data) - N + 1):
                data_points = data[i:i+N]
                new_data_point = self.mean(data_points)
                new_data_point = round(new_data_point, ndigits=2)
                smooth_data_array.append(new_data_point)
        elif technique == "mean" and n % 2 == 0: # Mean Smoothing for even number N
            temp_array = []
            for i in range(len(data) - N + 1):
                data_points = data[i:i+N]
                new_data_point = self.mean(data_points)
                new_data_point = round(new_data_point, ndigits=2)
                temp_array.append(new_data_point)
            
            # centres the data by averaging adjacent data points
            for j in range(len(temp_array) - 1): 
                first = temp_array[j]
                second = temp_array[j+1]
                new_data_point = self.mean([first,second])
                new_data_point = round(new_data_point, ndigits=2)
                smooth_data_array.append(new_data_point)
        elif technique == "median" and n % 2 != 0: # Median Smoothing for odd number N
            for i in range(len(data) - N + 1):
                data_points = data[i:i+N]
                new_data_point = median(data_points) # round not required, since it will always be the middle number
                smooth_data_array.append(new_data_point)
        elif technique == "median" and n % 2 == 0:
            temp_array = []
            for i in range(len(data) - N + 1):
                data_points = data[i:i+N]
                new_data_point = median(data_points)
                new_data_point = round(new_data_point, ndigits=2)
                temp_array.append(new_data_point)
            
            # centres the data by averaging adjacent data points
            for j in range(len(temp_array) - 1):
                first = temp_array[j]
                second = temp_array[j+1]
                new_data_point = median([first,second])
                new_data_point = round(new_data_point, ndigits=2)
                smooth_data_array.append(new_data_point)
        else:
            raise Exception("Code broken. Choices should be limited to [median,mean] and invalid N values should be caught beforehand.")
        
        return smooth_data_array 
    
    def write_to_output_file(self, file_output:str) -> None:
        '''Creates new CSV file and writes new data onto CSV file.'''
        final = pd.DataFrame({
            "time": self.time,
            "gps": self.gps,
            "gps_lat": self.gps_lat,
            "gps_long": self.gps_long,
            "gps_alt": self.gps_alt,
            "gps_course": self.gps_course,
            "gps_speed": self.gps_speed,
            "gps_satellites": self.gps_satellites,
            "aX": self.ax,
            "aY": self.ay,
            "aZ": self.az,
            "gX": self.gx,
            "gY": self.gy,
            "gZ": self.gz,
            "thermoC": self.thermoc,
            "tempF": self.thermof,
            "pot": self.pot,
            "cadence": self.cadence,
            "power": self.power,
            "reed_velocity": self.reed_velocity,
            "reed_distance": self.reed_distance
        })
        final.to_csv(file_output, index=False)
        print(f"Success! Output is written to {file_output}")

if __name__ == '__main__':
    data = pd.read_csv(args.input) # Loads and reads CSV file
    das_sort = DasSort(data, args.unit) # Filters data in CSV file
    das_sort.write_to_output_file(args.output) # Write filtered data into new CSV file
