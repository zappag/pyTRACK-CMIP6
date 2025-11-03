import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
import glob
import pickle
import os


import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


# dir with the vaia track to use as reference

ERA5_track_dir_vaia = f"/work/users/clima/ghinassi/track_output/ERA5/SON/msl/NH_ERA5_msl_6hr_2018_SON/dates/"
ERA5_track_vaia_filename = "ff_trs_neg.vaiagen_latgen38_longen4_radgen4_vaiapass_latpas45_lonpas8_radpas2"

ERA5_track_dir_florence = f"/work/users/clima/ghinassi/track_output/ERA5/SON/msl/NH_ERA5_msl_6hr_1966_SON/dates/"
ERA5_track_florence_filename = "ff_trs_neg.vaiapass_lat38_lon4_rad4_vaiapass_lat45_lon8_rad4_florence.txt"

#dir for z500 from ERA5
ERA5_z500_dir = "/home/ghinassi/work_big/ERA5/z500/grid_1x1/SON/"
z500_filename_vaia = "ERA5_z500_6hr_2018_SON.nc"
z500_filename_florence = "ERA5_z500_6hr_1966_SON.nc"
z500_filename_pattern = "ERA5_z500_6hr_*_SON.nc"

#dir for z500 from CMIP6
model_name = "EC-Earth3" # set to the model name you want to use
exp_name = "historical" # set to "historical" for the historical experiment, or to "scenarioMIP" for the scenarioMIP experiment
exp_type=None # set to None for the historical experiment, or to "ssp245" for the ssp245 experiment of the scenarioMIP

# Path to the CMIP6 z500 data
# Path with wildcard to loop over ensemble members
if exp_type is None:
    ensemble_dirs = sorted(glob.glob(f"/home/ghinassi/work_big/output/CMIP6/{exp_name}/{model_name}/6hrPt/atmos/6hrPlevPt/*/zg500/SON"))
elif exp_type is not None:
    ensemble_dirs = sorted(glob.glob(f"/home/ghinassi/work_big/output/CMIP6/{exp_name}/{model_name}/{exp_type}/6hrPt/atmos/6hrPlevPt/*/zg500/SON"))

#aprire tutti i files di z500 e calcolare l'index per ogni ens member poi salvarlo in un pickle file
#plot directory
plotdir= "/home/ghinassi/work/track_plots/z500_index/"

#directory for output index
pickle_dir="/home/ghinassi/work/similarity_pattern_index_pkl/"

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
    Convert longitude from 0-360 to -180 -- 180 deg.
    Handles both 'longitude' and 'lon' as coordinate names.
    """
    lon_name = 'longitude' if 'longitude' in _ds.coords else 'lon' if 'lon' in _ds.coords else None
    if lon_name is None:
        raise ValueError("Longitude coordinate not found. Expected 'longitude' or 'lon'.")

    if _ds[lon_name].min() >= 0:
        with xr.set_options(keep_attrs=True): 
            _ds.coords[lon_name] = (_ds[lon_name] + 180) % 360 - 180
        _ds = _ds.sortby(lon_name)
    return _ds

def convert180_360(_ds):
    """
    Convert longitude from -180 -- 180 to 0-360 deg.
    Handles both 'longitude' and 'lon' as coordinate names.
    """
    lon_name = 'longitude' if 'longitude' in _ds.coords else 'lon' if 'lon' in _ds.coords else None
    if lon_name is None:
        raise ValueError("Longitude coordinate not found. Expected 'longitude' or 'lon'.")

    if _ds[lon_name].min() < 0:
        with xr.set_options(keep_attrs=True): 
            _ds.coords[lon_name] = (_ds[lon_name] + 360) % 360
        _ds = _ds.sortby(lon_name)
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

    composite_z500= florence_z500
    composite_z500 = xr.concat([vaia_z500, florence_z500], dim='valid_time')
    composite_z500 = xr.concat([composite_z500.isel(valid_time=[0,2]).mean(dim='valid_time'), 
                                    composite_z500.isel(valid_time=[1,3]).mean(dim='valid_time')], 
                               dim='valid_time')
    
    #convert longitudes from 0-360 to -180-180
    
    composite_z500 = convert360_180(composite_z500)
    
    # now select lat lon box between lat1, lat2 and lon1, lon2
    
    composite_z500 = composite_z500.sel(latitude=slice(lat1, lat2), longitude=slice(lon1, lon2))

    return composite_z500

def compute_similarity_pattern_index(field, field_ref, lat1, lat2, lon1, lon2, save_to_pickle=False, pickle_filename=None):
    # Standardize coordinate names
    field = field.rename({'lat': 'latitude', 'lon': 'longitude'})

    # Ensure correct slicing order
    lat_min, lat_max = min(lat1, lat2), max(lat1, lat2)
    lon_min, lon_max = min(lon1, lon2), max(lon1, lon2)

    # Select the domain in both datasets
    field_domain = field.sel(latitude=slice(lat_min, lat_max), longitude=slice(lon_min, lon_max))
    
    # Interpolate field_ref onto the field grid
    field_ref_interp = field_ref.interp(latitude=field_domain.latitude, longitude=field_domain.longitude)
    field_ref_domain = field_ref_interp.sel(latitude=slice(lat_min, lat_max), longitude=slice(lon_min, lon_max))

    # Compute spatial anomaly (mean removed) for the reference field
    field_ref_prime = field_ref_domain - field_ref_domain.mean(dim=['latitude', 'longitude'])
    field_ref_vals = field_ref_prime.values

    # Prepare the output dictionary
    index_dict = {}

    for t in field_domain.time:
        # Extract and anomaly the field at time t
        field_t = field_domain.sel(time=t)
        field_prime_t = field_t - field_t.mean(dim=['latitude', 'longitude'])
        field_vals = field_prime_t.values

        # Handle NaNs
        mask = np.isfinite(field_vals) & np.isfinite(field_ref_vals)
        if np.sum(mask) == 0:
            similarity_index = np.nan
        else:
            numerator = np.sum(field_vals[mask] * field_ref_vals[mask])
            denominator = np.sum(field_ref_vals[mask] ** 2)
            similarity_index = numerator / denominator

        index_dict[str(t.values)] = similarity_index

    # Optional: Save to pickle
    if save_to_pickle and pickle_filename:
        with open(pickle_dir + pickle_filename, 'wb') as f:
            pickle.dump(index_dict, f)
        print(f"Similarity index saved to: {pickle_filename}")

    return index_dict


def plot_pdf_index(index, plotdir, ens_mean=False):
    # Extract the index values from the dictionary
    index_values = list(index.values())
    
    # Plot the PDF of the index values
    plt.hist(index_values, bins=20, color='blue', edgecolor='black', alpha=0.7, density=False)
    plt.xlabel('Pattern Similarity Index')
    plt.ylabel('Occurrences')
    
    if ens_mean:
        title = f'Pattern Similarity Index - {model_name} - {exp_name} - {exp_type} - ens_mean - SON'
        filename = f'pattern_index_{model_name}_{exp_name}_{exp_type}_ens_mean.png'
    else:
        title = f'Pattern Similarity Index - {model_name} - {exp_name} - {exp_type} - {ens_member} - SON'
        filename = f'pattern_index_{model_name}_{exp_name}_{exp_type}_{ens_member}.png'

    plt.title(title)
    plt.xlim(-1.5, 1.5)
    plt.savefig(os.path.join(plotdir, filename))
    plt.close()
    
    print("saved figure to", os.path.join(plotdir, filename))

    

#select lat lon box:
lon1=-15
lon2=25
lat1=60
lat2=30

#hours to consider before and after the max anomaly time
hours_shift = 48

vaia_track = read_ERA5_tracks(ERA5_track_dir_vaia, ERA5_track_vaia_filename)
florence_track = read_ERA5_tracks(ERA5_track_dir_florence, ERA5_track_florence_filename)
composite_z500 = get_composite_z500(vaia_track, florence_track, ERA5_z500_dir, z500_filename_vaia, z500_filename_florence, lat1, lat2, lon1, lon2, hours_shift)

plot_pdf = True
save_to_pickle = True
# Add this variable
ens_mean = True  # Set to True to read from existing pickle files and plot ensemble mean


if ens_mean:
    all_indexes = []
    ens_member_list = []  # <-- track ensemble member names

    for ens_dir in ensemble_dirs:
        ens_member = os.path.basename(os.path.dirname(os.path.dirname(ens_dir)))

        if exp_type is None:
            pickle_filename = f'index_pattern_{model_name}_{exp_name}_{ens_member}.pkl'
        else:
            pickle_filename = f'index_pattern_{model_name}_{exp_name}_{exp_type}_{ens_member}.pkl'

        pickle_path = os.path.join(pickle_dir, pickle_filename)

        if os.path.exists(pickle_path):
            print(f"Loading existing pickle for ens {ens_member} for experiment {exp_name} and type {exp_type}")
            with open(pickle_path, 'rb') as f:
                index_data = pickle.load(f)
        else:
            print(f"Pickle missing for {ens_member} for experiment {exp_name} and type {exp_type}, computing Similarity pattern index")
            z500_files = sorted(glob.glob(os.path.join(ens_dir, "*.nc")))
            if not z500_files:
                print(f"No files found for {ens_member}, skipping.")
                continue

            ds = xr.open_mfdataset(z500_files, combine='by_coords')
            ds = convert360_180(ds["zg500"])
            ds = ds.sel(lat=slice(lat2, lat1), lon=slice(lon1, lon2))

            index_data = compute_similarity_pattern_index(
                ds,
                composite_z500.isel(valid_time=0),
                lat1=45,
                lat2=35,
                lon1=lon1,
                lon2=lon2,
                save_to_pickle=True,
                pickle_filename=pickle_filename
            )

        all_indexes.append(index_data)
        # store the member name here
        ens_member_list.append(ens_member)  


    if all_indexes:
        all_values = []
        for d in all_indexes:
            all_values.extend([v for v in d.values() if v is not None and not np.isnan(v)])

        if plot_pdf:
            plot_pdf_index(dict(enumerate(all_values)), plotdir, ens_mean=True)
        if save_to_pickle:
            if exp_type is None:
                pickle_filename = f'index_pattern_{model_name}_{exp_name}_ens_members.pkl'
            else:
                pickle_filename = f'index_pattern_{model_name}_{exp_name}_{exp_type}_ens_members.pkl'

            ensemble_pickle_path = os.path.join(pickle_dir, pickle_filename)

            # Create dictionary mapping member names to their index dicts
            ens_members_dict = {f"member_{name}": index for name, index in zip(ens_member_list, all_indexes)}


            with open(ensemble_pickle_path, 'wb') as f:
                pickle.dump(ens_members_dict, f)

            print(f"Ensemble member similarity indexes saved to: {ensemble_pickle_path}")

    else:
        print("No valid data available for ensemble mean.")
