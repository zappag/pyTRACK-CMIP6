import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# this code reads the original and filtered tracks after the execution of the script pass_trajectories.sh.
# then it filters the tracks based on the spatial domain and plots the pdf distribution of the minimum sea level pressure of the total and filtered tracks.

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

def spatial_filter_tracks(tracks, lon_min, lon_max, lat_min, lat_max):
    # filters the tracks based on the spatial domain
    # tracks: dictionary with the tracks
    # lon_min, lon_max, lat_min, lat_max: float, minimum and maximum longitude and latitude of the domain
    
    filtered_tracks = {}
    
    for track_id in tracks:
        track_data = tracks[track_id]["data"]
        track_data_filtered = [(date, lon, lat, mslp) for date, lon, lat, mslp in track_data if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max]
        
        if track_data_filtered:
            filtered_tracks[track_id] = {
                "header": tracks[track_id]["header"],
                "data": track_data_filtered
            }
    
    return filtered_tracks


def plot_mslp_pdf(mslp_tot, mslp_filt1, plotdir, lon_min, lon_max, lat_min, lat_max):
    # plots the pdf distribution of the minimum sea level pressure of the total and filtered tracks
    # mslp_tot: dictionary with the total tracks
    # mslp_filt: dictionary with the filtered tracks
    
    mslp_tot_min = []
    mslp_filt1_min = []
    
    for track_id, track_data in mslp_tot.items():
        data = track_data["data"]
        mslp = [mslp for _, _, _, mslp in data]
        mslp_tot_min.append(max(mslp))
        
    for track_id, track_data in mslp_filt1.items():
        data = track_data["data"]
        mslp = [mslp for _, _, _, mslp in data]
        mslp_filt1_min.append(max(mslp)) 
        
        
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.hist(mslp_tot_min, bins=20, density=True, alpha=0.5, label=f"Total tracks (n={len(mslp_tot)})")
    ax.hist(mslp_filt1_min, bins=20, density=True, alpha=0.5, label=f"Double pass tracks (n={len(mslp_filt1)})")
    
    
    # Calculate and plot mean values and standard errors
    mean_tot = np.mean(mslp_tot_min)
    mean_filt1 = np.mean(mslp_filt1_min)
    
    std_err_tot = np.std(mslp_tot_min) / np.sqrt(len(mslp_tot_min))
    std_err_filt1 = np.std(mslp_filt1_min) / np.sqrt(len(mslp_filt1_min))

    
    ax.axvline(mean_tot, color='blue', linestyle='dashed', linewidth=1)
    ax.axvline(mean_filt1, color='orange', linestyle='dashed', linewidth=1)

    
    # Add text for mean values and standard errors
    ax.text(mean_tot, ax.get_ylim()[1]*0.9, f'Mean: {mean_tot:.2f} ± {std_err_tot:.2f}', color='blue')
    ax.text(mean_filt1, ax.get_ylim()[1]*0.8, f'Mean: {mean_filt1:.2f} ± {std_err_filt1:.2f}', color='orange')
    
    
    ax.set_title(f"MSLP anomaly distribution for between ({lat_min}-{lat_max}°N, {lon_min}-{lon_max}°E) for ERA5 - SON")
    ax.set_xlabel("Max mslp anomaly (hPa)")
    ax.set_ylabel("PDF")
    ax.legend()
    
    if not os.path.exists(plotdir):
        os.makedirs(plotdir)
    
    plt.savefig(plotdir+"mslp_pdf_doubplepass_ERA5.png")
    plt.close()
    print("saved plot in:", plotdir+"mslp_pdf_doublepass_ERA5.png")
    

ERA5_total_tracks = read_ERA5_tracks(ERA5_total_tracks_dir)
#ERA5_vaiagen_tracks = read_ERA5_tracks(ERA5_track_dir_vaia_analogue, filename="concatenated_tracks_latgen38_longen4_radgen4.txt")
#ERA5_vaiagen_vaiapass_tracks = read_ERA5_tracks(ERA5_track_dir_vaia_analogue, filename="concatenated_tracks_latgen38_longen4_radgen4_latpas45_lonpas8_radpas2.txt")

ERA5_doublepass = read_ERA5_tracks(ERA5_track_dir_vaia_analogue, filename="concatenated_tracks_firstlatpass38_firstlonpass4_firstrad4_secondlatpass45_secondlonpass8_secondrad4_1940-2024.txt")

#set lats and lons for the spatial filter
lon_min = 0
lon_max = 20
lat_min = 30
lat_max = 48

ERA5_total_tracks = spatial_filter_tracks(ERA5_total_tracks, lon_min, lon_max, lat_min, lat_max)
#ERA5_doublepass = spatial_filter_tracks(ERA5_doublepass, lon_min, lon_max, lat_min, lat_max)
#ERA5_vaiagen_tracks = spatial_filter_tracks(ERA5_vaiagen_tracks, lon_min, lon_max, lat_min, lat_max)
#ERA5_vaiagen_vaiapass_tracks = spatial_filter_tracks(ERA5_vaiagen_vaiapass_tracks, lon_min, lon_max, lat_min, lat_max)
plot_mslp_pdf(ERA5_total_tracks, ERA5_doublepass, plotdir, lon_min, lon_max, lat_min, lat_max)

