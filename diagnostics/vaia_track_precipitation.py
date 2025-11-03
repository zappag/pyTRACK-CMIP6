import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
from matplotlib.colors import ListedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# this code reads the filtered tracks after the execution of the script pass_trajectories.sh.
# The tracks are then plotted on a map.


# dir with the vaia track to use as reference

ERA5_track_dir_vaia = f"/home/ghinassi/work/track_output/ERA5/SON/msl/NH_ERA5_msl_6hr_1966_SON/dates/"
ERA5_track_vaia_filename = "ff_trs_neg.vaiapass_lat38_lon4_rad4_vaiapass_lat45_lon10_rad2"

# dir for mslp from ERA5

ERA5_mslp_dir = "/home/zappa/work/ERA5/hourly/mean_sea_level_pressure/6hrs/"
mslp_filename = "ERA5_mean_sea_level_pressure_6hrs_full_sfc_1966_70_-50_10_55.nc"

#dir for z500 from ERA5
ERA5_prec_dir = "/home/ghinassi/work_big/ERA5/total_precipitation/total_precipitation/6hT00/SON/"
precipitation_filename = "ERA5_total_precipitation_6hT00_1966_SON.nc"

plotdir= "/home/ghinassi/work/track_plots/vaia_analogue/"

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


def plot_track_and_prec(track_ref, ERA5_mslp_dir, mslp_filename, ERA5_prec_dir, prec_filename, plotdir, lat1=None, lat2=None, lon1=None, lon2=None):
    
    # Read the ERA5 mean sea level pressure data
    mslp_data = xr.open_dataset(os.path.join(ERA5_mslp_dir, mslp_filename))

    # Read the ERA5 precipitation data
    prec_data = xr.open_dataset(os.path.join(ERA5_prec_dir, prec_filename))

    # Extract the required variables
    lon_values_ERA = mslp_data["lon"]
    lat_values_ERA = mslp_data["lat"]
    mslp_values_ERA = mslp_data["MSL"]

    lon_values_prec = prec_data["lon"]
    lat_values_prec = prec_data["lat"]

    for track_id, track_data in track_ref.items():
        header_ref = track_data["header"]
        data_ref = track_data["data"]
        
        # Extract lon and lat values from track data
        lon_values_ref = [(lon + 180) % 360 - 180 for _, lon, _, _ in data_ref]
        lat_values_ref = [lat for _, _, lat, _ in data_ref]
        mslp_values_ref = [mslp for _, _, _, mslp in data_ref]

        # Create a PlateCarree projection
        projection = ccrs.PlateCarree()
        
        # Create a single subplot
        fig, ax = plt.subplots(1, 1, figsize=(10, 6), subplot_kw={"projection": projection})
        
        # Add the mslp field at the time step of minimum mslp value
        time_min_mslp = data_ref[mslp_values_ref.index(max(mslp_values_ref))][0]
        time_min_mslp = pd.to_datetime(time_min_mslp, format="%Y%m%d%H")
        cont1 = ax.contour(lon_values_ERA, lat_values_ERA, mslp_values_ERA.sel(time=time_min_mslp)/100, levels=np.arange(970, 1030.1, 10), cmap="gray", transform=projection)
        ax.plot(lon_values_ref[mslp_values_ref.index(max(mslp_values_ref))], lat_values_ref[mslp_values_ref.index(max(mslp_values_ref))], marker="o", color="blue", markersize=5, transform=projection, label="Min MSLP")
        ax.plot(lon_values_ref, lat_values_ref, color="black",
                linewidth=1.5,
                transform=projection,
                label="Vaia")

        
        # Add the cumulated precipitation between min mslp and plus and minus 24 hours 
        time_minus_24h = time_min_mslp - pd.Timedelta(hours=24)
        time_plus_24h = time_min_mslp + pd.Timedelta(hours=24)
        prec_values = prec_data["TP"].sel(time=slice(time_minus_24h, time_plus_24h)).sum(dim="time").values
        
        # Define custom colormap with white for the first interval
        cmap = plt.get_cmap("Blues")
        cmap_colors = cmap(np.arange(cmap.N))
        cmap_colors[0:10] = np.array([1, 1, 1, 1])  # Set the first color to white
        custom_cmap = ListedColormap(cmap_colors)
        
        cont2 = ax.contourf(lon_values_prec, lat_values_prec, prec_values*1000, levels=np.arange(0, 280.1, 10), cmap=custom_cmap, transform=projection)
        
        ax.set_title(f"MSLP and Total Precipitation around time: {time_min_mslp.strftime('%Y-%m-%d %H:%M')} UTC")
        # Add latitude and longitude ticks
        ax.set_xticks(range(-180, 181, 10), crs=projection)
        ax.set_yticks(range(-90, 91, 10), crs=projection)

        if lat1 and lat2 and lon1 and lon2:
            ax.set_extent([lon1, lon2, lat2, lat1], crs=projection)

        # Add labels
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

        # Add coastlines and continents
        #ax.add_feature(cfeature.LAND, color='lightgrey')
        ax.add_feature(cfeature.COASTLINE)
        # Add legend
        ax.legend()

        # Add a single colorbar for the entire figure
        cbar_ax = fig.add_axes([0.15, 0, 0.7, 0.02])  # Adjust the position to be more distant
        fig.colorbar(cont2, cax=cbar_ax, orientation='horizontal', label="Tot Precipitation (mm)")

        # Create the plot directory if it doesn't exist
        os.makedirs(plotdir, exist_ok=True)
        
        # Save plot
        plt.savefig(os.path.join(plotdir, f"mslp_total_prec_6h_{track_id}.png"), bbox_inches="tight")
        print(f"Saved plot with MSLP and precipitation in {plotdir} as mslp_total_prec_6h_{track_id}.png")

        plt.close()
        

vaia_track = read_ERA5_tracks(ERA5_track_dir_vaia, ERA5_track_vaia_filename)
plot_track_and_prec(vaia_track, ERA5_mslp_dir, mslp_filename, ERA5_prec_dir, precipitation_filename, plotdir, lat1=30, lat2=55, lon1=1, lon2=25)