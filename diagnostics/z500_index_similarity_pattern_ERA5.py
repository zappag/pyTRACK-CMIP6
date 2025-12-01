import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
from scipy.optimize import minimize_scalar
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pickle
#add cyclic point for plotting
from cartopy.util import add_cyclic_point

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


# dir with the vaia track to use as reference

ERA5_track_dir_vaia = f"/home/ghinassi/work/track_output/ERA5/SON/msl/NH_ERA5_msl_6hr_2018_SON/dates/"
ERA5_track_vaia_filename = "ff_trs_neg.vaiapass_lat39_lon4_rad3.5_vaiapass_lat45_lon10_rad3.5.box"

ERA5_track_dir_florence = f"/home/ghinassi/work/track_output/ERA5/SON/msl/NH_ERA5_msl_6hr_1966_SON/dates/"
ERA5_track_florence_filename = "ff_trs_neg.onlyflorence"

#dir for z500 from ERA5
#ERA5_z500_dir_gaussian = "/home/ghinassi/work_big/ERA5/z500_gaussian/"
ERA5_z500_dir = "/mnt/naszappa/ghinassi/ERA5/z500/grid_1x1/SON/"
z500_filename_vaia = "ERA5_z500_6hr_2018_SON.nc"
z500_filename_florence = "ERA5_z500_6hr_1966_SON.nc"
z500_filename_pattern = "ERA5_z500_6hr_*_SON.nc"


#plot directory
plotdir= "/home/ghinassi/work/track_plots/z500_index/"

#directory for output index
pickle_dir="/home/ghinassi/work/similarity_pattern_index_pkl/"
# create the directory if it does not exist
os.makedirs(pickle_dir, exist_ok=True)
ERA5_pickle_filename = "index_pattern_ERA5.pkl"

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

def convert360_180(_ds):
    """
    convert longitude from 0-360 to -180 -- 180 deg
    """
    # check if already 
    attrs = _ds['longitude'].attrs
    if _ds['longitude'].min() >= 0:
        with xr.set_options(keep_attrs=True): 
            _ds.coords['longitude'] = (_ds['longitude'] + 180) % 360 - 180
        _ds = _ds.sortby('longitude')
    return _ds

def convert180_360(_ds):
    """
    convert longitude from -180 -- 180 to 0-360 deg
    """
    # check if already 
    attrs = _ds['longitude'].attrs
    if _ds['longitude'].min() < 0:
        with xr.set_options(keep_attrs=True): 
            _ds.coords['longitude'] = (_ds['longitude'] + 360) % 360
        _ds = _ds.sortby('longitude')
    return _ds



def retrieve_z500_data(start_date, end_date, lat1, lat2, lon1, lon2):
    # Retrieve z500 data from ERA5 from a starting date to an end date
    # and between lat1, lat2 and lon1, lon2
    # Load the dataset
    files = [os.path.join(ERA5_z500_dir, f) for f in os.listdir(os.path.join(ERA5_z500_dir)) if f.startswith("ERA5_z500_6hr_") and f.endswith("_SON.nc")]
    ds = xr.open_mfdataset(files, combine='by_coords')
    
    # Convert geopotential to geopotential height and select 500 hPa level
    ds['z'] = ds["z"].sel(pressure_level=500) / 9.81
    
    ds = convert360_180(ds)
    
    # Select the data within the specified latitude/longitude bounds
    ds = ds.sel(latitude=slice(lat1, lat2), longitude=slice(lon1, lon2))
    
    # Select the data within the specified date range if provided
    if start_date and end_date:
        ds = ds.sel(valid_time=slice(start_date, end_date))
    
    return ds



def get_composite_z500(vaia_track, florence_track, ERA5_z500_dir, z500_filename_vaia, z500_filename_florence, lat1, lat2, lon1, lon2, hours_shift):
    
    def get_initial_and_max_anomaly_times(track):
        max_anomaly_time = max([point[0] for point in track[list(track.keys())[0]]["data"]])
        
        # initial time is the time 24 hours prior to the max anomaly time
        initial_time = pd.to_datetime(max_anomaly_time, format='%Y%m%d%H') - pd.Timedelta(hours=hours_shift)

        return pd.to_datetime(initial_time, format='%Y%m%d%H'), pd.to_datetime(max_anomaly_time, format='%Y%m%d%H')
 
    def get_z500_data(z500_filename, times):
        ds = xr.open_dataset(z500_filename)
        z500_values_ERA = ds["z"].sel(pressure_level=500, valid_time=times) / 9.81  # Convert geopotential to geopotential height
        
        return z500_values_ERA

    vaia_initial_time, vaia_max_anomaly_time = get_initial_and_max_anomaly_times(vaia_track)
    florence_initial_time, florence_max_anomaly_time = get_initial_and_max_anomaly_times(florence_track)
       
    vaia_z500 = get_z500_data(os.path.join(ERA5_z500_dir, z500_filename_vaia), [vaia_initial_time, vaia_max_anomaly_time])
    florence_z500 = get_z500_data(os.path.join(ERA5_z500_dir, z500_filename_florence), [florence_initial_time, florence_max_anomaly_time])
    # create a composite z500 by averaging the two events as the average of the first time step of each event
    # and the average of the second time step of each event
    # so that the composite has two time steps
    composite_z500 = xr.concat([ (vaia_z500.isel(valid_time=0) + florence_z500.isel(valid_time=0)) / 2,
                                 (vaia_z500.isel(valid_time=1) + florence_z500.isel(valid_time=1)) / 2], 
                                dim="valid_time")
    composite_z500 = composite_z500.assign_coords(valid_time=[f"composite_{hours_shift}_prior", "composite_max_anomaly_time"])
    
    #convert longitudes from 0-360 to -180-180
    
    composite_z500 = convert360_180(composite_z500)
    
    # now select lat lon box between lat1, lat2 and lon1, lon2
    
    composite_z500 = composite_z500.sel(latitude=slice(lat1, lat2), longitude=slice(lon1, lon2))

    return composite_z500


def compute_similarity_pattern_index(field, field_ref, lat1, lat2, lon1, lon2, save_to_pickle=False, pickle_filename=None):
    # Select the domain based on given latitude and longitude bounds
    field_ref_domain = field_ref.sel(latitude=slice(lat1, lat2), longitude=slice(lon1, lon2))
    field_domain = field.sel(latitude=slice(lat1, lat2), longitude=slice(lon1, lon2))
    
    # Compute the spatial mean and subtract it to get anomalies in the selected domain
    field_ref_prime = field_ref_domain - field_ref_domain.mean(dim=['latitude', 'longitude'])
    
    # Compute the similarity index for each time step
    index_dict = {}
    for t in field_domain.valid_time:
        field_prime_t = field_domain.sel(valid_time=t)
        similarity_index = np.sum(field_prime_t * field_ref_prime) / np.sum(field_ref_prime * field_ref_prime)
        index_dict[str(t.values)] = similarity_index["z"].values  # Convert time to string for dictionary keys and get the value
    
    # Save the dictionary to a pickle file if requested
    if save_to_pickle and pickle_filename:
        with open(os.path.join(pickle_dir, pickle_filename), 'wb') as f:
            pickle.dump(index_dict, f)
        print(f"Dictionary saved as pickle file in {os.path.join(pickle_dir, pickle_filename)}")
    
    return index_dict


def plot_similarity_pattern_index_ref(composite_z500, plotdir, title, plotname, lat_bounds=(30, 60), lon_bounds=(-15, 25)):

    lat1_box = 45
    lat2_box = 35


    """
    Plot the composite mean Z500 field of ERA5 reference state used to compute the similarity pattern index,
    """
    plt.figure(figsize=(8, 5))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # --- Compute the anomaly (subtract areal mean) ---
    field_anom = composite_z500.squeeze() - composite_z500.mean(dim=["latitude", "longitude"]).squeeze()

    # --- Plot color shading of absolute geopotential height ---
    im = composite_z500.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap="RdYlBu_r",
        vmin=5200,
        vmax=6000,
        add_colorbar=False,
    )

    # --- Add black contour lines for anomalies ---
    anomaly_levels = np.arange(-200, 201, 40)  # contour every 40 m anomaly
    # Add cyclic point to handle longitude wrapping
    field_cyclic, lon_cyclic = add_cyclic_point(field_anom, coord=composite_z500.longitude, axis=1)

    contours = ax.contour(
        lon_cyclic,
        composite_z500.latitude,
        field_cyclic,
        levels=anomaly_levels,
        colors='black',
        linewidths=1,
        transform=ccrs.PlateCarree(),
    )
    

    # --- Map features ---
    ax.coastlines(linewidth=1)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.LAND, facecolor='lightgray', zorder=0)
    ax.set_extent([lon_bounds[0], lon_bounds[1], lat_bounds[0], lat_bounds[1]], crs=ccrs.PlateCarree())
    
    #add 2 horizontal lines at lat1_box and lat2_box
    ax.plot([lon_bounds[0], lon_bounds[1]], [lat2_box, lat2_box], color='black', linestyle='--', transform=ccrs.PlateCarree())
    ax.plot([lon_bounds[0], lon_bounds[1]], [lat1_box, lat1_box], color='black', linestyle='--', transform=ccrs.PlateCarree())

    # --- Gridlines ---
    gl = ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False

    # --- Colorbar ---
    cbar = plt.colorbar(im, ax=ax, orientation="vertical", pad=0.02)
    cbar.set_label("Geopotential height (m)")

    # --- Title & Save ---
    plt.title(title, fontsize=11)
    outfile = os.path.join(plotdir, f"{plotname}.png")
    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved ERA5 reference plot: {outfile}")

def plot_pdf_index(index, plotdir):
    # Extract the index values from the dictionary
    index_values = list(index.values())
    
    # Plot the PDF of the index values
    plt.hist(index_values, bins=20, color='blue', edgecolor='black', alpha=0.7, density=False)
    plt.xlabel('Similarity Pattern Index')
    plt.ylabel('Occurrences')
    plt.title('Similarity Pattern Index - ERA5 (SON 1940-2024)')
    plt.xlim(-1.5, 1.5)
    plt.savefig(os.path.join(plotdir, 'similarity_pattern_index_ERA5.png'))
    print("saved figure to", os.path.join(plotdir, 'similarity_pattern_index_ERA5.png'))
    

#select lat lon box:
lon1=-15
lon2=25
lat1=60
lat2=30

#hours to consider before min mslp anomaly time to create composite of z500
hours_shift = 24

vaia_track = read_ERA5_tracks(ERA5_track_dir_vaia, ERA5_track_vaia_filename)
florence_track = read_ERA5_tracks(ERA5_track_dir_florence, ERA5_track_florence_filename)
composite_z500 = get_composite_z500(vaia_track, florence_track, ERA5_z500_dir, z500_filename_vaia, z500_filename_florence, lat1, lat2, lon1, lon2, hours_shift)

compute_index=False
if compute_index:
    z500_data = retrieve_z500_data(start_date=None, end_date=None, lat1=lat1, lat2=lat2, lon1=lon1, lon2=lon2)

    index_pattern_path = os.path.join(pickle_dir, ERA5_pickle_filename)

    if os.path.exists(index_pattern_path):
        print(f"Loading similarity index from {index_pattern_path}")
        with open(index_pattern_path, 'rb') as f:
            index_pattern = pickle.load(f)
    else:
        print("Pickle file not found. Computing similarity index...")
        index_pattern = compute_similarity_pattern_index(
            z500_data,
            composite_z500.isel(valid_time=0),
            lat1=45,
            lat2=35,
            lon1=lon1,
            lon2=lon2,
            save_to_pickle=True,
            pickle_filename=ERA5_pickle_filename
        )

    
plot_similarity_index_pattern=True
if plot_similarity_index_pattern:
    plot_similarity_pattern_index_ref(composite_z500.isel(valid_time=0), plotdir=plotdir,
                                    title="ERA5 z500 Composite Reference State",
                                    plotname="ERA5_z500_composite_reference_state_index_computation",
                                    lat_bounds=(lat2, lat1), lon_bounds=(lon1, lon2))

plot_pdf = False

if plot_pdf:
    plot_pdf_index(index_pattern, plotdir)


