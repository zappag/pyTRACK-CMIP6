import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from datetime import date, timedelta
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# select a confidence level for the cyclone tracks
CL=2
ERA5_medcyclones_file = "/home/ghinassi/work/MedCyclones/data/TRACKS_CL"+str(CL)+".dat"
ERA5_mslp_dir = "/home/zappa/work/ERA5/hourly/mean_sea_level_pressure/6hrs/"
mslp_filename = "ERA5_mean_sea_level_pressure_6hrs_full_sfc_2018_70_-50_10_55.nc"

plotdir= "/home/ghinassi/work/diagnostics/plots/medcyclones/CL"+str(CL)+"/"

"""
### info about medcyclones data: ###

Each row corresponds to a single track point, while the eight columns provide the following information:

 Column 1 provides a cumulatively increasing index that functions as an identifier of unique cyclone tracks. For instance, all information about the track of cyclone no. 456 is found in all rows starting with the number 456.
 Column 2 provides the longitude of track points.
 Column 3 provides the latitude of track points. It is important to note that geographical coordinates are produced using step 2 of our method and thus may not match the exact location of grid points of ERA5.
 Column 4 provides the year of occurrence.
 Column 5 provides the month of occurrence.
 Column 6 provides the day of occurrence.
 Column 7 provides the hour of occurrence in UTC.
 Column 8 provides the lowest MSLP value within a 2.5∘ radius from the geographical coordinates in columns 2 and 3. 
These values are only meant to function as an approximate reference of intensity. 
Indeed, geographical coordinates of composite track points in columns 2 and 3 are located in the average location of track points of individual CDTMs. Therefore, values in column 8 may not necessarily correspond to the deepest MSLP or the highest relative vorticity of the tracks.
"""

def read_ERA5_medcyclones_tracks(ERA5_medcyclones_file):
    tracks = {}
    
    with open(ERA5_medcyclones_file, 'r') as file:

        for line in file:
            if line.startswith('#'):
                continue
            
            track_id, lon, lat, year, month, day, hour, mslp = line.strip().split()
            
            if track_id not in tracks:
                tracks[track_id] = {
                    "header": {
                        "TRACK_ID": track_id,
                        "START_TIME": f"{year}-{month}-{day} {hour}",
                        "POINT_NUM": 0
                    },
                    "data": []
                }
            
            tracks[track_id]["data"].append((f"{year}-{month}-{day} {hour}", float(lon), float(lat)))
            tracks[track_id]["header"]["POINT_NUM"] += 1
    
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
            if np.datetime64(date[0:10] + 'T' + date[11:]).astype('datetime64[s]') == np.datetime64(time_values[t].values).astype('datetime64[s]'):
                lons_values_track = [track["lon"] for track in track_data]# if track["date"] == np.datetime64(time_values[t].values).astype('datetime64[s]')]
                lats_values_track = [track["lat"] for track in track_data]# if track["date"] == np.datetime64(time_values[t].values).astype('datetime64[s]')]
                
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
            

tracks = read_ERA5_medcyclones_tracks(ERA5_medcyclones_file)

#tracks = filter_tracks(tracks, min_duration=48)

#for each time step in the track files create a dictionary with all lat and lot pairs found at that time step
tracks = reorder_tracks(tracks)

plot_mslp_and_tracks(ERA5_mslp_dir, mslp_filename, tracks, plotdir, startdate="2018-10-26-00", enddate="2018-11-04-00")

