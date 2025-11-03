import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from datetime import date, timedelta
import cartopy.crs as ccrs
import cartopy.feature as cfeature

#ERA5_track_dir = "/home/zappa/work_big/TRACK_tracks/ERA5/ERA5_VOR850_1hr_oct-mar20132014_DET/dates"
ERA5_track_dir = "/home/ghinassi/work/track_output/ERA5/SON/vor850/NH_ERA5_uv_6hr_1966_SON_merged/dates/"
ERA5_track_filename="tr_trs_pos"
ERA5_mslp_dir = "/home/zappa/work/ERA5/hourly/mean_sea_level_pressure/6hrs/"
mslp_filename = "ERA5_mean_sea_level_pressure_6hrs_full_sfc_1966_70_-50_10_55.nc"

plotdir= "/home/ghinassi/work/diagnostics/plots/mslp_and_tracks/vor850_6hour-T42_pytrack/"

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
                    track_data.append((date, lon, lat))

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
                        track_data.append((date, lon, lat))

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

def filter_tracks(tracks, min_duration):
    filtered_tracks = {}
    
    for track_id, track_data in tracks.items():
        header = track_data["header"]
        point_num = header["POINT_NUM"]
        data = track_data["data"]
        
        # Check if track lasts for at least N hours
        if point_num >= min_duration:
            filtered_tracks[track_id] = track_data
    
    return filtered_tracks


def reorder_tracks(tracks):
    reordered_tracks = {}
    
    for track_id, track_data in tracks.items():
        data = track_data["data"]
        
        for date, lon, lat in data:
            if date not in reordered_tracks:
                reordered_tracks[date] = []
            reordered_tracks[date].append({"date": date, "lat": lat, "lon": lon})
    
    return reordered_tracks

def plot_tracks(tracks, plotdir, startdate=None, enddate=None, lat1=None, lat2=None, lon1=None, lon2=None):
    for track_id, track_data in tracks.items():
        header = track_data["header"]
        data = track_data["data"]
        
        # Extract lon and lat values from track data
        lon_values = [lon for _, lon, _ in data]
        lat_values = [lat for _, _, lat in data]

        # Create a PlateCarree projection
        projection = ccrs.PlateCarree()
        
        # Create a figure and axes with PlateCarree projection
        fig, ax = plt.subplots(subplot_kw={'projection': projection})

        # Filter tracks based on startdate and enddate
        if startdate and enddate:
            filtered_data = [(date, lon, lat) for date, lon, lat in data if pd.to_datetime(startdate, format="%Y%m%d%H").date() <= pd.to_datetime(date, format="%Y%m%d%H").date() <= pd.to_datetime(enddate, format="%Y%m%d%H").date()]
            lon_values = [lon for _, lon, _ in filtered_data]
            lat_values = [lat for _, _, lat in filtered_data]
        else:
            filtered_data = data
        
        # Filter tracks based on lat1, lat2, lon1, lon2
        if lat1 and lat2 and lon1 and lon2:
            filtered_data = [(date, lon, lat) for date, lon, lat in data if lat1 <= lat <= lat2 and lon1 <= lon <= lon2]
            lon_values = [lon for _, lon, _ in filtered_data]
            lat_values = [lat for _, _, lat in filtered_data]
        else:
            filtered_data = data

        # Plot track as scatter points if the filtered data is not empty
        if filtered_data:
            ax.scatter(lon_values, lat_values, color="black",
                        s=15,
                        linewidths=0.5,
                        marker=".",
                        alpha=0.8,
                        transform=projection)

            # Add latitude and longitude ticks
            ax.set_xticks(range(-180, 181, 30), crs=projection)
            ax.set_yticks(range(-90, 91, 10), crs=projection)

            if lat1 and lat2 and lon1 and lon2:
                ax.set_extent([lon1, lon2, lat2, lat1], crs=projection)

            # Add labels
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")

            # Add coastlines and continents
            ax.add_feature(cfeature.LAND, color='lightgrey')

            ax.set_title("Track ID: {}, Start Time: {}".format(header["TRACK_ID"], header["START_TIME"]))
            
            # Show plot
            plt.savefig(plotdir + "track_{}.png".format(header["START_TIME"]))
            print("saved plot for track ID: ", header["TRACK_ID"], " and start time: ", header["START_TIME"])

            plt.close()

def plot_mslp_and_tracks(ERA5_mslp_dir, mslp_filename, tracks, plotdir, startdate=None, enddate=None):
    # Read the ERA5 mean sea level pressure data
    mslp_data = xr.open_dataset(os.path.join(ERA5_mslp_dir, mslp_filename))

    # Extract the required variables
    lon_values_ERA = mslp_data["lon"]
    lat_values_ERA = mslp_data["lat"]
    mslp_values_ERA = mslp_data["MSL"]

    # Select the range of time steps
    mslp_values_ERA = mslp_values_ERA.sel(time=slice(startdate, enddate))
    time_values = mslp_values_ERA["time"]

    # Create a PlateCarree projection
    projection = ccrs.PlateCarree()

    for t in range(len(time_values)):
       
        # Create a figure and axes with PlateCarree projection
        fig, ax = plt.subplots(subplot_kw={'projection': projection})
        
        # Plot the mslp values as a contour plot
        contour = ax.contour(lon_values_ERA, lat_values_ERA, mslp_values_ERA[t,:,:]/100, levels=np.arange(970,1030.1,3), cmap="coolwarm", transform=projection)
        
        # Add colorbar
        cbar = plt.colorbar(contour)
        cbar.set_label("Mean Sea Level Pressure (hPa)")
        
        # Add latitude and longitude ticks
        ax.set_xticks(range(-180, 180, 30), crs=projection)
        ax.set_yticks(range(-90, 90, 30), crs=projection)
        ax.set_extent([-30, 30, 65, 30], crs=projection)
        # Add labels
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        
        # Add coastlines and continents
        ax.add_feature(cfeature.LAND, color='lightgrey')
    
        # Add title
        ax.set_title(f'mslp and tracks at Time: {pd.to_datetime(time_values[t].values, format="%Y-%m-%d%H")}', fontsize=8)
        
        # Plot tracks for the current time step
        for date, track_data in tracks.items():
            # all lats and lons as scatter points at the timestep of the netcdf file
            if np.datetime64(date[:4] + '-' + date[4:6] + '-' + date[6:8] + 'T' + date[8:10]).astype('datetime64[s]') == np.datetime64(time_values[t].values).astype('datetime64[s]'):
                
                lons_values_track = [track["lon"] for track in track_data if track["date"] == date]
                lats_values_track = [track["lat"] for track in track_data if track["date"] == date]
                ax.scatter(lons_values_track, lats_values_track, color="black",
                    s=15,
                    transform=projection)
                
        # Create a folder if it does not exist
        folder_name = f"{plotdir}/{startdate}_{enddate}"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        
        # Save the plot if a track is found
        plt.savefig(f"{folder_name}/mslp_and_tracks_{pd.to_datetime(time_values[t].values, format='%Y%m%d%H')}.png")
        print("saved mslp + track plot for time: ", pd.to_datetime(time_values[t].values, format='%Y%m%d%H'))
        
        plt.close()
            

tracks = read_ERA5_tracks(ERA5_track_dir, ERA5_track_filename)
#tracks = filter_tracks(tracks, min_duration=48)
#for each time step in the track files create a dictionary with all lat and lot pairs found at that time step
tracks = reorder_tracks(tracks)

plot_mslp_and_tracks(ERA5_mslp_dir, mslp_filename, tracks, plotdir, startdate="1966-11-03-00", enddate="1966-11-06-00")

