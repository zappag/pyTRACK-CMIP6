import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# this code reads the filtered tracks after the execution of the script pass_trajectories.sh.
# then the min mslp anomaly for each track is plotted in a time series.

var="msl"
seas="SON"

# dir with the concatenated tracks

ERA5_total_tracks_dir="/home/ghinassi/work/track_output/ERA5/SON/msl/total_tracks"

# dir with the vaia-like filtered tracks

ERA5_track_dir_vaia_analogue = "/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue"

# dir for mslp from ERA5


plotdir= "/home/ghinassi/work/diagnostics/plots/mslp_pdf/"

def read_ERA5_tracks(ERA5_track_dir, filename=None):
    """
    Reads ERA5 track data from a specified directory or file.
    Parameters:
    ERA5_track_dir (str): The directory containing the ERA5 track files.
    filename (str, optional): The specific file to read from the directory. If not provided, all files in the directory will be read.
    Returns:
    dict: A dictionary where the keys are track IDs and the values are dictionaries containing track headers and data.
          The header dictionary contains:
              - "TRACK_ID": The track ID.
              - "START_TIME": The start time of the track.
              - "POINT_NUM": The number of points in the track.
          The data list contains tuples of (date, longitude, latitude, mean sea level pressure).
    """
    
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
                    lon = float(data[1])
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
                        lon = float(data[1])
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

def plot_min_mslp_timeseries(ERA5_vaiagen_vaiapass_tracks, plotdir, var, seas):
    
    plt.figure(figsize=(10, 6))
    
    for track_id, track in ERA5_vaiagen_vaiapass_tracks.items():
        track_data = track["data"]
        times = range(len(track_data))
        mslp_values = [point[3] for point in track_data]
        if track_id == 2208:
            plt.plot(times, mslp_values, marker='o', linestyle='-', color='black', label='Vaia')
        else:
            plt.plot(times, mslp_values, marker='o', linestyle='-', color='lightgray')
    
    plt.title(f"Vaialike tracks min MSLP Time Series ({var} - {seas})")
    plt.xlabel("Time Step")
    plt.ylabel("MSLP (hPa)")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(plotdir, f"min_mslp_timeseries_{var}_{seas}.png"))
    print("saved plot:", os.path.join(plotdir, f"min_mslp_timeseries_{var}_{seas}.png"))
    plt.close()


    
    
ERA5_vaiagen_vaiapass_tracks = read_ERA5_tracks(ERA5_track_dir_vaia_analogue, filename="concatenated_tracks_latgen38_longen4_radgen4_latpas45_lonpas8_radpas2.txt")
plot_min_mslp_timeseries(ERA5_vaiagen_vaiapass_tracks, plotdir, var, seas)

