import pickle
import os
import pandas as pd
import numpy as np
from datetime import datetime

import os
import pickle
import pandas as pd
from datetime import datetime
import sys

class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

# Start logging to file and console
log_file_path="/home/ghinassi/work/track_plots/summary_index_probability/"
log_filename = "storm_givenlargescale_ERA5.txt"
sys.stdout = Logger(os.path.join(log_file_path, log_filename))

"""
This script analyzes ERA5 weather tracks and computes the probability of having a track 
given an index value above a specified threshold. It reads index values from a pickle file, 
filters ERA5 tracks based on timestamps corresponding to high index values, and calculates 
the probability of track occurrence. The script also includes utility functions for longitude 
conversion and ERA5 track data parsing.

Functions:
- get_timestamps_above_threshold: Extracts timestamps with index values above a given threshold.
- convert_lon: Converts longitude from 0-360 to -180 to 180 format.
- convert_lon180_360: Converts longitude from -180 to 180 to 0-360 format.
- read_ERA5_tracks: Reads and parses ERA5 track data from a directory or file.
- filter_tracks_by_threshold: Filters ERA5 tracks based on timestamps above a threshold.
"""

index_path = "/home/ghinassi/work/similarity_pattern_index_pkl/index_pattern_ERA5.pkl"

ERA5_tracks_path = "/home/ghinassi/work/track_output/ERA5/SON/msl/total_tracks/"
ERA5_tracks_filename = "concatenated_tracks.txt"
filtered_tracks_path="/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue/"
filtered_tracks_filename = "concatenated_tracks_firstlatpass38_firstlonpass4_firstrad4_secondlatpass45_secondlonpass8_secondrad4.txt"

def get_all_timestamps():
    """
    Processes index data from a pickle file, resamples it to daily mean values, 
    and formats the timestamps into a specific string format.
    The function performs the following steps:
    1. Reads index data from a pickle file.
    2. Converts the data into a pandas DataFrame for easier manipulation.
    3. Resamples the data to calculate daily mean values based on timestamps.
    4. Formats the timestamps into the 'YYYYMMDDHH' string format.
    5. Returns the formatted data as a list of tuples containing the formatted 
       timestamp and the corresponding index value.
    Returns:
        list of tuple: A list where each tuple contains:
            - formatted_timestamp (str): The timestamp in 'YYYYMMDDHH' format.
            - index_value (float): The daily mean index value.
    """
    # Open the pickle file and read the data
    with open(index_path, 'rb') as file:
        data = pickle.load(file)

    # Convert the data to a DataFrame for easier manipulation
    df = pd.DataFrame(list(data.items()), columns=['timestamp', 'index_value'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Resample the data to daily mean
    daily_mean_df = df.resample('D', on='timestamp').mean()

    # Convert the timestamps to the desired format
    formatted_data = []
    for timestamp, index_value in daily_mean_df.itertuples(index=True):
        formatted_timestamp = timestamp.strftime('%Y%m%d%H')
        formatted_data.append((formatted_timestamp, index_value))
    
    return formatted_data

def get_timestamps_above_threshold(threshold=0.9):
    # Open the pickle file and read the data
    with open(index_path, 'rb') as file:
        data = pickle.load(file)

    # Convert the data to a DataFrame for easier manipulation
    df = pd.DataFrame(list(data.items()), columns=['timestamp', 'index_value'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Resample the data to daily mean
    daily_mean_df = df.resample('D', on='timestamp').mean()

    # Filter the timestamps based on the threshold and convert the format
    filtered_data = []
    for timestamp, index_value in daily_mean_df.itertuples(index=True):
        if index_value > threshold:
            formatted_timestamp = timestamp.strftime('%Y%m%d%H')
            filtered_data.append((formatted_timestamp, index_value))
    
    return filtered_data

def convert_lon(lon):
    if (lon > 180):
        lon -= 360
    return lon

def convert_lon180_360(lon):
    if (lon < 0):
        lon += 360
    return lon

def read_ERA5_tracks(ERA5_track_dir, filename=None):
    
    tracks = {}
    
    if filename:
        track_id = None
        track_data = []
        with open(os.path.join(ERA5_track_dir, filename), "r") as file:
            for line in file:
                line = line.strip()
                if line.startswith("0") or line.startswith("TRACK_NUM"):
                    continue
                elif line.startswith("TRACK_ID"):
                    track_id = int(line.split()[1])
                    #print("Track ID:", track_id)
                    start_time = int(line.split()[-1])
                    continue
                elif line.startswith("POINT_NUM"):
                    num_points = int(line.split()[1])
                    #print("Number of points:", num_points)
                    continue
                elif line:
                    data = line.split()
                    date = data[0]
                    lon = convert_lon(float(data[1]))
                    lat = float(data[2])
                    mslp = float(data[3])
                    track_data.append((date, lon, lat, mslp))

                if len(track_data) == num_points:
                    tracks[track_id] = {
                        "header": {
                            "TRACK_ID": track_id,
                            "START_TIME": start_time,
                            "POINT_NUM": num_points
                        },
                        "data": track_data
                    }
                    #print("Header:", tracks[track_id]["header"])
                    #print("Data (lon, lat):", [(lon, lat) for _, lon, lat in track_data])
                    track_id = None
                    track_data = []
    else:
        for filename in os.listdir(ERA5_track_dir):
            track_id = None
            track_data = []
            
            with open(os.path.join(ERA5_track_dir, filename), "r") as file:
                for line in file:
                    line = line.strip()
                    if line.startswith("0") or line.startswith("TRACK_NUM"):
                        continue
                    elif line.startswith("TRACK_ID"):
                        track_id = int(line.split()[1])
                        #print("Track ID:", track_id)
                        continue
                    elif line.startswith("POINT_NUM"):
                        num_points = int(line.split()[1])
                        #print("Number of points:", num_points)
                        continue
                    elif line:
                        data = line.split()
                        date = data[0]
                        lon = convert_lon(float(data[1]))
                        lat = float(data[2])
                        mslp = float(data[3])
                        track_data.append((date, lon, lat, mslp))

                    if len(track_data) == num_points:
                        tracks[track_id] = {
                            "header": {
                                "TRACK_ID": track_id,
                                "START_TIME": data[0],
                                "POINT_NUM": num_points
                            },
                            "data": track_data
                        }
                        #print("Header:", tracks[track_id]["header"])
                        #print("Data (lon, lat):", [(lon, lat) for _, lon, lat in track_data])
                        track_id = None
                        track_data = []
    
    return tracks

def filter_tracks_by_threshold(ERA5_tracks, timestamps_above_threshold, delta_time=0):
    if delta_time > 0:
        # Create a set of valid timestamps within the delta_time range
        timestamps_set = set()
        for timestamp, _ in timestamps_above_threshold:
            timestamps_set.update(
                {timestamp, (datetime.strptime(timestamp, '%Y%m%d%H') + pd.Timedelta(hours=delta_time)).strftime('%Y%m%d%H')}
            )
    else:
        # Extract only the timestamps from the threshold data for faster lookup
        timestamps_set = {timestamp for timestamp, _ in timestamps_above_threshold}

    # Filter tracks that have at least one matching timestamp within the range
    filtered_tracks = {
        track_id: track_info
        for track_id, track_info in ERA5_tracks.items()
        if any(point[0] in timestamps_set for point in track_info["data"])
    }

    return filtered_tracks

# get the time stamp above the selected threshold
threshold = 0.9
timestamps_above_threshold = get_timestamps_above_threshold(threshold)

# now print the time stamps above the threshold and the index value
#for timestamp, index_value in timestamps_above_threshold:
    #print(f"Timestamp: {timestamp}, Index Value: {index_value}")
    
# Read the filtered tracks timestamps from the file

ERA5_tracks = read_ERA5_tracks(ERA5_tracks_path)
ERA5_tracks_vaiapass= read_ERA5_tracks(filtered_tracks_path)

filtered_tracks = filter_tracks_by_threshold(ERA5_tracks, timestamps_above_threshold, delta_time=48)
# now get the Vaia/Florence tracks in which the time stamp is above the threshold (resolution is 6 hours)
filtered_tracks_vaiapass = filter_tracks_by_threshold(ERA5_tracks_vaiapass, timestamps_above_threshold, delta_time=48)

# compute the probability of having a vaia/florence z500 pattern as the ratio between the total number of timesteps in the index 
# and the timesteps in which the index is above the threshold
# for simplicity we assume that the index is above the threshold for 1 day so a daily mean is performed

probability_large_scale= len(timestamps_above_threshold)/len(get_all_timestamps())
print("Timestamps above the threshold:", len(timestamps_above_threshold))
print("Total number of timestamps:", len(get_all_timestamps()))
print("Probability of having a large scale pattern in z500 similar to Vaia/Florence:", probability_large_scale)

# now compute the probability of having a track given the large scale as the ratio
# between the number of tracks with the index over the threshold which follow a track similar to Vaia/Florence
# and all the time stamps with a z500 field over the threshold
probability_storm = len(filtered_tracks_vaiapass)/len(timestamps_above_threshold)
print("Tracks above thre threshold similar to Vaia/Florence:", len(filtered_tracks_vaiapass))
print("Timestamps above the threshold:", len(timestamps_above_threshold))
# 
print("Probability of having a track given the z500 index over the threshold:", probability_storm)

