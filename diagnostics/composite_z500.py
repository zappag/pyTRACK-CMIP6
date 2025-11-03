import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# this code reads the filtered tracks after the execution of the script pass_trajectories.sh.
# The tracks are then plotted on a map.


# dir with the vaia track to use as reference

ERA5_track_dir_vaia = f"/home/ghinassi/work/track_output/ERA5/SON/msl/NH_ERA5_msl_6hr_2018_SON/dates/"
ERA5_track_vaia_filename = "ff_trs_neg.vaiapass_lat38_lon4_rad4_vaiapass_lat45_lon10_rad2"
ERA5_track_dir_florence = f"/home/ghinassi/work/track_output/ERA5/SON/msl/NH_ERA5_msl_6hr_1966_SON/dates/"
ERA5_track_florence_filename = "ff_trs_neg.vaiapass_lat38_lon4_rad4_vaiapass_lat45_lon10_rad2"

#dir for z500 from ERA5
ERA5_z500_dir = "/home/ghinassi/work_big/ERA5/z500/grid_1x1/SON/"
z500_filename_vaia = "ERA5_z500_6hr_2018_SON.nc"
z500_filename_florence = "ERA5_z500_6hr_1966_SON.nc"

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

def plot_z500_composite(vaia_track, florence_track, ERA5_z500_dir, z500_filename_vaia, z500_filename_florence, plotdir, lat1, lat2, lon1, lon2):
    
    def get_initial_and_min_mslp_times(track):
        """Extract initial time and time of minimum MSLP from track data."""
        data = track[list(track.keys())[0]]["data"]
        df = pd.DataFrame(data, columns=["date", "lon", "lat", "mslp"])
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d%H')
        df['mslp'] = pd.to_numeric(df['mslp'])

        initial_time = df['date'].iloc[0]
        min_mslp_time = df.loc[df['mslp'].idxmin(), 'date']
        
        return initial_time, min_mslp_time
 
    def get_z500_data(z500_filename, times):
        """Read Z500 data for given times."""
        ds = xr.open_dataset(z500_filename)
        
        # Check for the correct time variable name
        time_var = 'time' if 'time' in ds.dims else 'valid_time'
        
        z500_values = ds["z"].sel({time_var: times}) / 9.80665  # Convert geopotential to geopotential height
        z500_values = z500_values.assign_coords({time_var: times})  # Ensure time labels are correct
        
        return z500_values

    def plot_track(ax, track, label, color):
        """Plot cyclone track on map."""
        for track_id, track_info in track.items():
            lons = [point[1] for point in track_info["data"]]
            lats = [point[2] for point in track_info["data"]]
            ax.plot(lons, lats, marker='o', label=label, color=color, linewidth=2)
    
    # Get key times for both tracks
    vaia_initial_time, vaia_min_mslp_time = get_initial_and_min_mslp_times(vaia_track)
    florence_initial_time, florence_min_mslp_time = get_initial_and_min_mslp_times(florence_track)
       
    # Read Z500 fields
    vaia_z500 = get_z500_data(os.path.join(ERA5_z500_dir, z500_filename_vaia), [vaia_initial_time, vaia_min_mslp_time])
    florence_z500 = get_z500_data(os.path.join(ERA5_z500_dir, z500_filename_florence), [florence_initial_time, florence_min_mslp_time])

    # Combine and compute composites
    composite_z500 = xr.concat([vaia_z500, florence_z500], dim='valid_time')

    composite_initial = 0.5*(composite_z500.isel(valid_time=0) + composite_z500.isel(valid_time=2)).squeeze()
    composite_min_mslp = 0.5*(composite_z500.isel(valid_time=1) + composite_z500.isel(valid_time=3)).squeeze()


    # Subset to plotting region
    composite_initial = composite_initial.sel(latitude=slice(lat1, lat2), longitude=slice(lon1, lon2))
    composite_min_mslp = composite_min_mslp.sel(latitude=slice(lat1, lat2), longitude=slice(lon1, lon2))

    # Plot
    fig, axes = plt.subplots(1, 2, subplot_kw={'projection': ccrs.PlateCarree()}, figsize=(15, 7))
    
    titles = ['Composite Z500 at Initial Time (48h before min MSLP)', 'Composite Z500 at Min MSLP']

    for ax, composite, title in zip(axes, [composite_initial, composite_min_mslp], titles):
        ax.set_extent([lon1, lon2, lat1, lat2], crs=ccrs.PlateCarree())
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        
        im = composite.plot.contourf(ax=ax, transform=ccrs.PlateCarree(), cmap='coolwarm', levels=20, add_colorbar=False)
        plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.05, label='Z500 (m)')
        
        plot_track(ax, vaia_track, 'Vaia Track', 'black')
        plot_track(ax, florence_track, 'Florence Track', 'gray')
        
        ax.set_title(title)
        ax.legend()

    plt.tight_layout()
    output_path = os.path.join(plotdir, 'composite_z500_vaia_florence.png')
    plt.savefig(output_path)
    plt.close()
    print("Saved figure at:", output_path)

    

vaia_track = read_ERA5_tracks(ERA5_track_dir_vaia, ERA5_track_vaia_filename)
florence_track = read_ERA5_tracks(ERA5_track_dir_florence, ERA5_track_florence_filename)

#plot z500 composite
plot_z500_composite(vaia_track, florence_track, ERA5_z500_dir, z500_filename_vaia, z500_filename_florence, plotdir, 50, 30, 0.1, 25)
