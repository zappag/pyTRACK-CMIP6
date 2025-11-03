import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
from scipy.stats import gaussian_kde
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# this code reads the total concatenated tracks from ERA5 and plots the track density, genesis and lysis points

var="msl"
seas="SON"

# dir with the vaia track to use as reference

ERA5_track_dir = f"/home/ghinassi/work/track_output/ERA5/{seas}/{var}/total_tracks/"

plotdir= "/home/ghinassi/work/track_plots/total_tracks/ERA5/"

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
                    lon = float(data[1])
                    lat = float(data[2])
                    track_data.append((date, lon, lat))

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

        
def plot_track_density(alltracks, plotdir, lat1=None, lat2=None, lon1=None, lon2=None):
    # plot track density of all tracks
    # Create a PlateCarree projection
    projection = ccrs.PlateCarree()
    
    # Create a figure and axes with PlateCarree projection
    fig, ax = plt.subplots(subplot_kw={'projection': projection}, figsize=(10, 6))

    # Handle all tracks for density plotting
    if alltracks:
        # Collect all longitude and latitude values for KDE
        all_lon_values, all_lat_values = [], []
        for track_id, track_data in alltracks.items():
            header = track_data["header"]
            data = track_data["data"]
            
            # Extract lon and lat values from track data
            all_lon_values += [(lon + 180) % 360 - 180 for _, lon, _ in data]
            all_lat_values += [lat for _, _, lat in data]

        # Perform KDE to get a smooth density field
        xy = np.vstack([all_lon_values, all_lat_values])
        kde = gaussian_kde(xy, bw_method=0.1)  # Bandwidth adjustment for smoothness
        
        # Create grid for evaluation
        lon_grid, lat_grid = np.meshgrid(np.arange(lon1, lon2, 0.05),
                                         np.arange(lat1, lat2, 0.05))
        
        # Evaluate KDE on the grid
        density = kde(np.vstack([lon_grid.ravel(), lat_grid.ravel()])).reshape(lon_grid.shape)

        # Plot the density as a smooth continuous field
        c = ax.pcolormesh(lon_grid, lat_grid, density, shading='auto', cmap='viridis', alpha=0.6, transform=projection)
        
        # Add colorbar to show density scale
        cbar = plt.colorbar(c, ax=ax, orientation='vertical', pad=0.02, label="Track Density")

    # Add latitude and longitude ticks
    ax.set_xticks(range(-180, 181, 30), crs=projection)
    ax.set_yticks(range(-90, 91, 10), crs=projection)

    # Set the map extent if boundaries are provided
    if lat1 and lat2 and lon1 and lon2:
        ax.set_extent([lon1, lon2, lat1, lat2], crs=projection)

    # Add labels
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Add coastlines and continents
    ax.add_feature(cfeature.LAND, color='lightgrey')

    # Add title
    ax.set_title("Track Density (Var: {} - Seas: {} - ERA5)".format(var, seas))
    
    # Create the plot directory if it doesn't exist
    os.makedirs(plotdir, exist_ok=True)
    
    # Save plot
    plt.savefig(plotdir + f"trackdensity_ERA5.png")
    print("saved plot named: ", plotdir + f"trackdensity_ERA5.png")
    plt.close()
        
def plot_track_genesis(alltracks, plotdir, lat1=None, lat2=None, lon1=None, lon2=None):
    # plot genesis points of all tracks
    # Create a PlateCarree projection
    projection = ccrs.PlateCarree()
    
    # Create a figure and axes with PlateCarree projection
    fig, ax = plt.subplots(subplot_kw={'projection': projection}, figsize=(10, 6))

    # Handle all tracks for genesis points plotting
    if alltracks:
        # Collect all genesis points
        genesis_lon_values, genesis_lat_values = [], []
        for track_id, track_data in alltracks.items():
            header = track_data["header"]
            data = track_data["data"]
            
            # Extract lon and lat values from track data
            genesis_lon_values.append((data[0][1] + 180) % 360 - 180)
            genesis_lat_values.append(data[0][2])

        # Plot genesis points
        ax.scatter(genesis_lon_values, genesis_lat_values, color="red",
                    s=15,
                    linewidths=0.5,
                    marker="o",
                    alpha=0.8,
                    transform=projection)

    # Add latitude and longitude ticks
    ax.set_xticks(range(-180, 181, 30), crs=projection)
    ax.set_yticks(range(-90, 91, 10), crs=projection)

    # Set the map extent if boundaries are provided
    if lat1 and lat2 and lon1 and lon2:
        ax.set_extent([lon1, lon2, lat1, lat2], crs=projection)

    # Add labels
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Add coastlines and continents
    ax.add_feature(cfeature.LAND, color='lightgrey')

    # Add title
    ax.set_title("Genesis Points (Var: {} - Seas: {} - ERA5)".format(var, seas))
    
    # Create the plot directory if it doesn't exist
    os.makedirs(plotdir, exist_ok=True)
    
    # Save plot
    plt.savefig(plotdir + f"genesispoints_ERA5.png")
    print("saved plot named: ", plotdir + f"genesispoints_ERA5.png")
    plt.close()
    
def plot_track_lysis(alltracks, plotdir, lat1=None, lat2=None, lon1=None, lon2=None):
    # plot lysis points of all tracks
    # Create a PlateCarree projection
    projection = ccrs.PlateCarree()
    
    # Create a figure and axes with PlateCarree projection
    fig, ax = plt.subplots(subplot_kw={'projection': projection}, figsize=(10, 6))

    # Handle all tracks for lysis points plotting
    if alltracks:
        # Collect all lysis points
        lysis_lon_values, lysis_lat_values = [], []
        for track_id, track_data in alltracks.items():
            header = track_data["header"]
            data = track_data["data"]
            
            # Extract lon and lat values from track data
            lysis_lon_values.append((data[-1][1] + 180) % 360 - 180)
            lysis_lat_values.append(data[-1][2])

        # Plot lysis points
        ax.scatter(lysis_lon_values, lysis_lat_values, color="blue",
                    s=15,
                    linewidths=0.5,
                    marker="o",
                    alpha=0.8,
                    transform=projection)

    # Add latitude and longitude ticks
    ax.set_xticks(range(-180, 181, 30), crs=projection)
    ax.set_yticks(range(-90, 91, 10), crs=projection)

    # Set the map extent if boundaries are provided
    if lat1 and lat2 and lon1 and lon2:
        ax.set_extent([lon1, lon2, lat1, lat2], crs=projection)

    # Add labels
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Add coastlines and continents
    ax.add_feature(cfeature.LAND, color='lightgrey')

    # Add title
    ax.set_title("Lysis Points (Var: {} - Seas: {} - ERA5)".format(var, seas))
    
    # Create the plot directory if it doesn't exist
    os.makedirs(plotdir, exist_ok=True)
    
    # Save plot
    plt.savefig(plotdir + f"lysispoints_ERA5.png")
    print("saved plot named: ", plotdir + f"lysispoints_ERA5.png")
    plt.close()
    
def spatial_filter_tracks(tracks, lon_min, lon_max, lat_min, lat_max, added_field_tp=False):
    filtered_tracks = {}
    
    for track_id in tracks:
        track_data = tracks[track_id]["data"]

        track_data_filtered = [(date, lon, lat) for date, lon, lat in track_data if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max]
        
        if track_data_filtered:
            filtered_tracks[track_id] = {
                "header": tracks[track_id]["header"],
                "data": track_data_filtered
            }
    
    return filtered_tracks
        

if __name__ == "__main__":
    
    use_stats_from_TRACK = True
    
    if use_stats_from_TRACK == False:
        
        # if use_stats_from_TRACK is False, then read the ERA5 tracks and plot the statistics
        # track density genesys etc... are computed and plotted with python
    
        # Read the ERA5 tracks
        ERA5_tracks = read_ERA5_tracks(ERA5_track_dir, filename="concatenated_tracks.txt")
        
        lon_min = 0.1
        lon_max = 20
        lat_min = 30
        lat_max = 48
        
        #ERA5_tracks = spatial_filter_tracks(ERA5_tracks, lon_min, lon_max, lat_min, lat_max, added_field_tp=False)
        
        # Plotting track density
        plot_track_density(ERA5_tracks, plotdir, lat1=lat_min, lat2=lat_max, lon1=lon_min, lon2=lon_max)
        # Plotting genesis points
        plot_track_genesis(ERA5_tracks, plotdir, lat1=lat_min, lat2=lat_max, lon1=lon_min, lon2=lon_max)
        # Plotting lysis points
        plot_track_lysis(ERA5_tracks, plotdir, lat1=lat_min, lat2=lat_max, lon1=lon_min, lon2=lon_max)
        
    elif use_stats_from_TRACK == True:
        
        # now use the statistics computed from TRACK
        stats_file="/home/ghinassi/work/track_output/ERA5/SON/msl/stats/ff_trs_neg_scl.std_1984-2014_1.nc"
        
        def plot_stats_from_TRACK(stats_file, plotdir):
            # Open the netCDF file
            ds = xr.open_dataset(stats_file)
            
            # Extract the required fields
            mstr = ds['mstr']
            tden = ds['tden']
            gden = ds['gden']
            lden = ds['lden']
            
            # Mask mean intensity where track density is less than or equal to 1
            mstr = mstr.where(tden > 1)
            
            # Define the extent for the Euro-Atlantic sector in the Northern Hemisphere
            extent = [-90, 40, 35, 80]  # [lon_min, lon_max, lat_min, lat_max]
            # Create a PlateCarree projection
            projection = ccrs.NorthPolarStereo(central_longitude=0)
            
            # Create a figure with subplots
            fig, axes = plt.subplots(2, 2, subplot_kw={'projection': projection}, figsize=(15, 10))
            
            # Plot mean intensity
            mstr.plot(ax=axes[0, 0], transform=ccrs.PlateCarree(), cmap='Reds', vmin=0, vmax=28, cbar_kwargs={'label': 'Mean Intensity', 'shrink': 0.8, 'extend': 'max'})
            axes[0, 0].set_title('Mean Intensity')
            axes[0, 0].coastlines()
            axes[0, 0].set_extent(extent, crs=ccrs.PlateCarree())
            
            # Plot track density
            tden.plot(ax=axes[0, 1], transform=ccrs.PlateCarree(), cmap='Reds', vmin=0, vmax=14, cbar_kwargs={'label': 'Track Density', 'shrink': 0.8, 'extend': 'max'})
            axes[0, 1].set_title('Track Density')
            axes[0, 1].coastlines()
            axes[0, 1].set_extent(extent, crs=ccrs.PlateCarree())
            
            # Plot genesis density
            gden.plot(ax=axes[1, 0], transform=ccrs.PlateCarree(), cmap='Reds', vmin=0, vmax=3, cbar_kwargs={'label': 'Genesis Density', 'shrink': 0.8, 'extend': 'max'})
            axes[1, 0].set_title('Genesis Density')
            axes[1, 0].coastlines()
            axes[1, 0].set_extent(extent, crs=ccrs.PlateCarree())
            
            # Plot lysis density
            lden.plot(ax=axes[1, 1], transform=ccrs.PlateCarree(), cmap='Reds', vmin=0, vmax=3, cbar_kwargs={'label': 'Lysis Density', 'shrink': 0.8, 'extend': 'max'})
            axes[1, 1].set_title('Lysis Density')
            axes[1, 1].coastlines()
            axes[1, 1].set_extent(extent, crs=ccrs.PlateCarree())
            
            # Add a general title for the figure
            fig.suptitle('ERA5 stats (1984-2014) - SON', fontsize=16)
            
            # Adjust layout
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            
            # Create the plot directory if it doesn't exist
            os.makedirs(plotdir, exist_ok=True)
            
            # Save plot
            plt.savefig(plotdir + f"track_stats_from_TRACK_ERA5_{seas}.png")
            print("saved plot named: ", plotdir + f"track_stats_from_TRACK_ERA5_{seas}.png")
            plt.close()

        # Call the function to plot stats from TRACK
        plot_stats_from_TRACK(stats_file, plotdir)
        
        
        
        
    