import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.util import add_cyclic_point

# this code reads the filtered tracks after the execution of the script pass_trajectories.sh.
# The tracks are then plotted on a map.


# dir with the vaia track to use as reference

ERA5_track_dir_vaia = f"/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue/"
ERA5_track_vaia_filename = "concatenated_tracks_lat38_lon4_rad4_lat45_lon8_rad4_1940-2024.txt"
var="msl"  #var used for TRACK can be "msl" or vor850
target_track_id = 2208  # Change this to the desired track ID 2573 is nov 1966, 2208 is Vaia 2018
# dir for mslp from ERA5
ERA5_mslp_dir = "/mnt/naszappa/ERA5/hourly/mean_sea_level_pressure/6hrs/"
#dir for z500 from ERA5
ERA5_z500_dir = "/home/ghinassi/nas_zappa/naszappa/ghinassi/ERA5/z500_gaussian/"
if target_track_id == 2208:
    mslp_filename = "ERA5_mean_sea_level_pressure_6hrs_full_sfc_2018_70_-50_10_55.nc"
    z500_filename = "ERA5_z500_6hr_2018.nc"
    name_storm = "Vaia"
elif target_track_id == 2573:
    mslp_filename = "ERA5_mean_sea_level_pressure_6hrs_full_sfc_1966_70_-50_10_55.nc"
    z500_filename = "ERA5_z500_6hr_1966.nc"
    name_storm = "November 1966"


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


def plot_track_msl(track_ref, ERA5_mslp_dir, mslp_filename, plotdir, lat1=None, lat2=None, lon1=None, lon2=None, storm_name="Florence"):
    
    # Read the ERA5 mean sea level pressure data
    mslp_data = xr.open_dataset(os.path.join(ERA5_mslp_dir, mslp_filename))

    # Extract the required variables
    lon_values_ERA = mslp_data["lon"]
    lat_values_ERA = mslp_data["lat"]
    mslp_values_ERA = mslp_data["MSL"]

    for track_id, track_data in track_ref.items():
        header_ref = track_data["header"]
        data_ref = track_data["data"]
        
        # Extract lon and lat values from track data
        lon_values_ref = [(lon + 180) % 360 - 180 for _, lon, _, _ in data_ref]
        lat_values_ref = [lat for _, _, lat, _ in data_ref]
        mslp_values_ref = [mslp for _, _, _, mslp in data_ref]

        # Create a PlateCarree projection
        projection = ccrs.PlateCarree()
        
        # Create subplots
        fig, axs = plt.subplots(1, 3, figsize=(18, 6), subplot_kw={"projection": projection})
        
        # Add the mslp field at the time step of genesis
        time_genesis = header_ref["START_TIME"]
        time_genesis = pd.to_datetime(time_genesis, format="%Y%m%d%H")
        cont1 = axs[0].contour(lon_values_ERA, lat_values_ERA, mslp_values_ERA.sel(time=time_genesis)/100, levels=np.arange(970,1030.1,3), cmap="coolwarm", transform=projection)
        axs[0].plot(lon_values_ref[0], lat_values_ref[0], marker="o", color="red", markersize=5, transform=projection, label="Genesis")
        axs[0].plot(lon_values_ref, lat_values_ref, color="black",
                linewidth=1.5,
                transform=projection,
                label=storm_name)
        axs[0].set_title("Genesis, time: " + str(time_genesis))
        
        # Add the mslp field at the time step of minimum mslp value
        time_min_mslp = data_ref[mslp_values_ref.index(max(mslp_values_ref))][0]
        time_min_mslp = pd.to_datetime(time_min_mslp, format="%Y%m%d%H")
        print("time_min_mslp", time_min_mslp, "min mslp value", 1013 - max(mslp_values_ref))
        cont2 = axs[1].contour(lon_values_ERA, lat_values_ERA, mslp_values_ERA.sel(time=time_min_mslp)/100, levels=np.arange(970,1030.1,3), cmap="coolwarm", transform=projection)
        axs[1].plot(lon_values_ref[mslp_values_ref.index(max(mslp_values_ref))], lat_values_ref[mslp_values_ref.index(max(mslp_values_ref))], marker="o", color="blue", markersize=5, transform=projection, label="Min MSLP")
        axs[1].plot(lon_values_ref, lat_values_ref, color="black",
                linewidth=1.5,
                transform=projection,
                label=storm_name)
        axs[1].set_title(f"Minimum MSLP: {1013 - max(mslp_values_ref)} hPa, time: {str(time_min_mslp)}")
        
        # Add the mslp field at the last time step (end of track)
        time_end_track = data_ref[-1][0]
        time_end_track = pd.to_datetime(time_end_track, format="%Y%m%d%H")
        print("time_end_track", time_end_track)
        cont3 = axs[2].contour(lon_values_ERA, lat_values_ERA, mslp_values_ERA.sel(time=time_end_track)/100, levels=np.arange(970,1030.1,3), cmap="coolwarm", transform=projection)
        axs[2].plot(lon_values_ref[-1], lat_values_ref[-1], marker="o", color="green", markersize=5, transform=projection, label="End of track")
        axs[2].plot(lon_values_ref, lat_values_ref, color="black",
                linewidth=1.5,
                transform=projection,
                label=storm_name)
        axs[2].set_title("End of Track, time: " + str(time_end_track))
        
        for ax in axs:
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
            ax.add_feature(cfeature.COASTLINE)
            # Add legend
            ax.legend()

        # Add a single colorbar for the entire figure
        cbar_ax = fig.add_axes([0.15, 0.1, 0.7, 0.02])
        fig.colorbar(cont3, cax=cbar_ax, orientation='horizontal', pad=0.05, label="mslp (hPa)")

        # Create the plot directory if it doesn't exist
        os.makedirs(plotdir, exist_ok=True)
        
        # Save plot
        plt.savefig(os.path.join(plotdir, f"multiplot_{track_id}_{var}.png"), bbox_inches="tight")
        print(f"Saved plot named multiplot_{track_id}_{var}.png in {plotdir} for track {track_id} with mslp")

        plt.close()
        
def plot_tracks_z500(track_ref, ERA5_z500_dir, z500_filename, plotdir, lat1=None, lat2=None, lon1=None, lon2=None, storm_name="Vaia"):
        # Read the ERA5 geopotential height data
        z500_data = xr.open_dataset(os.path.join(ERA5_z500_dir, z500_filename))

        # Extract the required variables
        lon_values_ERA = z500_data["longitude"]
        lat_values_ERA = z500_data["latitude"]
        z500_values_ERA = z500_data["z"].sel(pressure_level=500) / 9.80665  # Convert geopotential to geopotential height

        for track_id, track_data in track_ref.items():
            header_ref = track_data["header"]
            data_ref = track_data["data"]
            
            # Extract lon and lat values from track data
            lon_values_ref = [(lon + 180) % 360 - 180 for _, lon, _, _ in data_ref]
            lat_values_ref = [lat for _, _, lat, _ in data_ref]
            mslp_values_ref = [mslp for _, _, _, mslp in data_ref]

            # Create a PlateCarree projection
            projection = ccrs.PlateCarree()
            
            # Create subplots
            fig, axs = plt.subplots(1, 3, figsize=(18, 6), subplot_kw={"projection": projection})
            
            # Add the z500 field at the time step of genesis
            time_genesis = header_ref["START_TIME"]
            time_genesis = pd.to_datetime(time_genesis, format="%Y%m%d%H")
            cont1 = axs[0].contour(lon_values_ERA, lat_values_ERA, z500_values_ERA.sel(valid_time=time_genesis)/10, levels=np.arange(480, 600.1, 5), cmap="coolwarm", transform=projection)
            axs[0].plot(lon_values_ref[0], lat_values_ref[0], marker="o", color="red", markersize=5, transform=projection, label="Genesis")
            axs[0].plot(lon_values_ref, lat_values_ref, color="black",
                    linewidth=1.5,
                    transform=projection,
                    label=storm_name)
            axs[0].set_title("Genesis, time: " + str(time_genesis))
            
            # Add the z500 field at the time step of minimum z500 value

            time_min_mslp = data_ref[mslp_values_ref.index(max(mslp_values_ref))][0]
            time_min_mslp = pd.to_datetime(time_min_mslp, format="%Y%m%d%H")
            cont2 = axs[1].contour(lon_values_ERA, lat_values_ERA, z500_values_ERA.sel(valid_time=time_min_mslp)/10, levels=np.arange(480, 600.1, 5), cmap="coolwarm", transform=projection)
            axs[1].plot(lon_values_ref[mslp_values_ref.index(max(mslp_values_ref))], lat_values_ref[mslp_values_ref.index(max(mslp_values_ref))], marker="o", color="blue", markersize=5, transform=projection, label="Min mslp")
            axs[1].plot(lon_values_ref, lat_values_ref, color="black",
                    linewidth=1.5,
                    transform=projection,
                    label=storm_name)
            axs[1].set_title("z500 at min mslp, time: " + str(time_min_mslp))
            
            # Add the z500 field at the last time step (end of track)
            time_end_track = data_ref[-1][0]
            time_end_track = pd.to_datetime(time_end_track, format="%Y%m%d%H")
            print("time_end_track", time_end_track)
            cont3 = axs[2].contour(lon_values_ERA, lat_values_ERA, z500_values_ERA.sel(valid_time=time_end_track)/10, levels=np.arange(480, 600.1, 5), cmap="coolwarm", transform=projection)
            axs[2].plot(lon_values_ref[-1], lat_values_ref[-1], marker="o", color="green", markersize=5, transform=projection, label="End of track")
            axs[2].plot(lon_values_ref, lat_values_ref, color="black",
                    linewidth=1.5,
                    transform=projection,
                    label=storm_name)
            axs[2].set_title("End of Track, time: " + str(time_end_track))
            
            for ax in axs:
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
                ax.add_feature(cfeature.COASTLINE)
                # Add legend
                ax.legend()

            # Add a single colorbar for the entire figure
            cbar_ax = fig.add_axes([0.15, 0.1, 0.7, 0.02])
            fig.colorbar(cont3, cax=cbar_ax, orientation='horizontal', pad=0.05, label="z500 (gpm)")

            # Create the plot directory if it doesn't exist
            os.makedirs(plotdir, exist_ok=True)
            
            # Save plot
            plt.savefig(os.path.join(plotdir, f"multiplot_{track_id}_z500.png"), bbox_inches="tight")
            print(f"Saved plot in {plotdir} for track {track_id} with z500")

            plt.close()

def plot_combined_z500_mslp(track_ref, ERA5_z500_dir, z500_filename, ERA5_mslp_dir, mslp_filename, storm_name,
                            plotdir, lat1=None, lat2=None, lon1=None, lon2=None):

    # Read ERA5 data
    z500_data = xr.open_dataset(os.path.join(ERA5_z500_dir, z500_filename))
    mslp_data = xr.open_dataset(os.path.join(ERA5_mslp_dir, mslp_filename))

    # Extract variables
    lon_z = z500_data["longitude"]
    lat_z = z500_data["latitude"]
    z500 = z500_data["z"].sel(pressure_level=500) / 9.81  # convert geopotential → height

    lon_m = mslp_data["lon"]
    lat_m = mslp_data["lat"]
    mslp = mslp_data["MSL"]
    
    # Prepare cyclic points for z500 and mslp
    z500_cp, lon_z_cp = add_cyclic_point(z500.values, coord=lon_z)
    mslp_cp, lon_m_cp = add_cyclic_point(mslp.values, coord=lon_m)

    for track_id, track_data in track_ref.items():
        header_ref = track_data["header"]
        data_ref = track_data["data"]

        # Track coordinates
        lon_ref = [(lon + 180) % 360 - 180 for _, lon, _, _ in data_ref]
        lat_ref = [lat for _, _, lat, _ in data_ref]
        mslp_ref = [mslp for _, _, _, mslp in data_ref]

        # Key times
        #time_genesis = pd.to_datetime(header_ref["START_TIME"], format="%Y%m%d%H")
        time_min_mslp = pd.to_datetime(data_ref[mslp_ref.index(max(mslp_ref))][0], format="%Y%m%d%H")
        time_genesis = time_min_mslp - pd.Timedelta(hours=24)
        projection = ccrs.PlateCarree()
        fig, axs = plt.subplots(1, 2, figsize=(14, 6), subplot_kw={"projection": projection})

        for ax, (time_label, current_time, marker_color, marker_label) in zip(
            axs,
            [
                ("24 h prior to mslp", time_genesis, "red", "24 h prior to MSLP"),
                ("Min MSLP", time_min_mslp, "blue", "Min MSLP"),
            ],
        ):
            # Select fields
            z500_field = z500.sel(valid_time=current_time)
            mslp_field = mslp.sel(time=current_time) / 100  # to hPa
            
                # Prepare cyclic points for z500 and mslp
            z500_cp, lon_z_cp = add_cyclic_point(z500_field.values, coord=lon_z)
            mslp_cp, lon_m_cp = add_cyclic_point(mslp_field.values, coord=lon_m)

            # Plot z500 shading
            cf = ax.contourf(lon_z_cp, lat_z, z500_cp, levels=np.arange(4800, 6000.1, 100),
                             cmap="RdYlBu_r", transform=projection, extend="both")

            # Overlay mslp contour lines
            cs = ax.contour(lon_m_cp, lat_m, mslp_cp, levels=np.arange(990, 1031, 10),
                            colors="darkgrey", linewidths=2.5, transform=projection)
            ax.clabel(cs, inline=False, fontsize=10, colors="black", fmt="%d")

            # Plot track only +- 48 hours before and after the min mslp time
            lon_ref_subset = []
            lat_ref_subset = []
            for t, lon, lat, _ in data_ref:
                t_dt = pd.to_datetime(t, format="%Y%m%d%H")
                if time_min_mslp - pd.Timedelta(hours=48) <= t_dt <= time_min_mslp + pd.Timedelta(hours=48):
                    lon_ref_subset.append((lon + 180) % 360 - 180)
                    lat_ref_subset.append(lat)
            ax.plot(lon_ref_subset, lat_ref_subset, color="k", linewidth=1.8, transform=projection, label=storm_name)
            # Track time array
            track_times = [pd.to_datetime(t, format="%Y%m%d%H") for t, _, _, _ in data_ref]
            # Find index of current time in track times
            try:
                idx = track_times.index(current_time)
            except ValueError:
                print(f"Time {current_time} not found in track times for track ID {track_id}. Skipping marker plot.")
                continue

            # Plot marker at correct position
            ax.plot(
                lon_ref[idx],
                lat_ref[idx],
                marker="o",
                color=marker_color,
                markersize=6,
                transform=projection,
                label=marker_label
            )

            ax.set_title(f"{current_time.strftime('%Y-%m-%d %H:%M')} UTC", fontsize=18)

            # Map setup
            ax.coastlines()
            ax.add_feature(cfeature.LAND, color="lightgrey")
            ax.add_feature(cfeature.BORDERS, linewidth=0.5)
            gl = ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)
            gl.top_labels = False
            gl.right_labels = False
            ax.tick_params(axis='both', labelsize=16)
            if lat1 and lat2 and lon1 and lon2:
                ax.set_extent([lon1, lon2, lat2, lat1], crs=projection)
            ax.legend()

        # Colorbar for z500
        cbar_ax = fig.add_axes([0.15, 0.1, 0.7, 0.02])
        cbar = fig.colorbar(cf, cax=cbar_ax, orientation="horizontal")
        cbar.set_label("z500 (m)", fontsize=18)   # ← enlarge label font here
        # font size for colorbar ticks
        cbar_ax.tick_params(labelsize=16)

        os.makedirs(plotdir, exist_ok=True)
        outfile = os.path.join(plotdir, f"combined_z500_mslp_{track_id}_{storm_name.replace(' ', '_')}.png")
        plt.savefig(outfile, bbox_inches="tight")
        plt.close()
        print(f"Saved combined mslp and z500 plot: {outfile}")

    

all_tracks = read_ERA5_tracks(ERA5_track_dir_vaia, ERA5_track_vaia_filename)
vaia_track = {track_id: all_tracks[track_id] for track_id in all_tracks if track_id == target_track_id}
plot_combined_z500_mslp(
    vaia_track,
    ERA5_z500_dir,
    z500_filename,
    ERA5_mslp_dir,
    mslp_filename,
    name_storm,
    plotdir,
    lat1=30, lat2=65, lon1=-20, lon2=30,
)
