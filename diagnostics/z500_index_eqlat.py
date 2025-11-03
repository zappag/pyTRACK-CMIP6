import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
from scipy.optimize import minimize_scalar
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


# dir with the vaia track to use as reference

ERA5_track_dir_vaia = f"/work/users/clima/ghinassi/track_output/ERA5/SON/msl/NH_ERA5_msl_6hr_2018_SON/dates/"
ERA5_track_vaia_filename = "ff_trs_neg.vaiagen_latgen38_longen4_radgen4_vaiapass_latpas45_lonpas8_radpas2"

ERA5_track_dir_florence = f"/work/users/clima/ghinassi/track_output/ERA5/SON/msl/NH_ERA5_msl_6hr_1966_SON/dates/"
ERA5_track_florence_filename = "ff_trs_neg.vaiapass_lat38_lon4_rad4_vaiapass_lat45_lon8_rad4_florence.txt"

#dir for z500 from ERA5
ERA5_z500_dir = "/work_big/users/clima/ghinassi/ERA5/z500/"
z500_filename_vaia = "ERA5_z500_6hr_2018.nc"
z500_filename_florence = "ERA5_z500_6hr_1966.nc"

plotdir= "/home/ghinassi/work/track_plots/vaia_analogue/"

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

    composite_z500 = xr.concat([vaia_z500, florence_z500], dim='valid_time')
    composite_z500 = xr.concat([composite_z500.isel(valid_time=[0,2]).mean(dim='valid_time'), 
                                    composite_z500.isel(valid_time=[1,3]).mean(dim='valid_time')], 
                               dim='valid_time')
    
    #convert longitudes from 0-360 to -180-180
    
    composite_z500 = convert360_180(composite_z500)
    
    # now select lat lon box between lat1, lat2 and lon1, lon2
    
    #composite_z500 = composite_z500.sel(latitude=slice(lat1, lat2), longitude=slice(lon1, lon2))

    return composite_z500

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


def integrate_contour_area(lons, lats, earth_radius):
    """
    Compute the area enclosed by a contour using proper longitude integration and latitude weighting.
    """
    # Convert to radians
    lats_rad = np.deg2rad(lats)
    lons_rad = np.deg2rad(lons)

    # Ensure longitudes are in [0, 360] range
    lons_rad = np.mod(lons_rad, 2 * np.pi)

    # Compute differential longitude 
    dlon = abs(np.diff(lons_rad)[0])
    
    #compute differential latitude
    dlat = abs(np.diff(lats_rad)[0])
    
    # Compute area bounded by z500 contour with cos(latitude) weighting
    area = 0
    area =  np.trapz(earth_radius**2 * np.cos(lats_rad) * dlon * dlat)
    
    return abs(area)  # Ensure positive area

def equivalent_latitude_contour(z500, lat_ref):
    """
    Find the geopotential height contour that encloses the same area as the region north of lat_ref.
    """
    earth_radius = 6371.0 * 10**3  # Earth radius in meters
    lat_ref_rad = np.deg2rad(lat_ref)
    area_north_lat_ref = 2 * np.pi * earth_radius**2 * (1 - np.sin(lat_ref_rad))  # Area of the region north of lat_ref

    def area_difference(contour_level):
        # Generate contour plot to extract paths
        contour=0
        contour = z500.plot.contour(levels=[contour_level], add_colorbar=False)
        plt.close()  # Prevent unwanted plot display

        paths = contour.collections[0].get_paths()
        contour_area = 0

        for path in paths:
            vertices = path.vertices
            lons = vertices[:, 0]
            lats = vertices[:, 1]
            contour_area = integrate_contour_area(lons, lats, earth_radius)

        print(f"Contour level: {contour_level}, Contour area: {contour_area}, Target area: {area_north_lat_ref}")
        return abs(contour_area - area_north_lat_ref)

    # Find optimal contour level that minimizes area difference
    result = minimize_scalar(area_difference, bounds=(z500.min(), z500.max()), method='bounded')
    result = result.x
    return float(result)

def calculate_max_meridional_deviation(composite_z500, lat_ref, lon1, lon2):
    """
    Calculate the maximum meridional displacement of the geopotential height contour 
    to the south of the reference latitude (lat_ref) within a given longitude range (lon1 to lon2).
    
    Handles longitude inputs in both [-180, 180] and [0, 360] ranges.
    """

    max_deviation_timeseries = []
    contour_levels = []

    # Normalize longitude boundaries to [0, 360]
    lon1 = (lon1 + 360) % 360 if lon1 < 0 else lon1
    lon2 = (lon2 + 360) % 360 if lon2 < 0 else lon2

    for time in composite_z500.valid_time:
        print("Valid time:", time)
        z500_at_time = composite_z500.sel(valid_time=time)
        
        # Compute the equivalent latitude contour level
        contour_level = equivalent_latitude_contour(z500_at_time, lat_ref=lat_ref)
        contour_levels.append(contour_level)

        # Extract contours
        contour_set = z500_at_time.plot.contour(levels=[contour_level], add_colorbar=False)
        plt.close()  # Avoid unnecessary plots

        if not contour_set.collections or not contour_set.collections[0].get_paths():
            print(f"No contour found at level {contour_level} for time {time}")
            continue  # Skip this iteration if no valid contour is found

        contour_paths = contour_set.collections[0].get_paths()
        max_deviation = 0  # Initialize max deviation

        for path in contour_paths:
            vertices = path.vertices
            lons = np.mod(vertices[:, 0], 360)  # Convert longitudes to [0, 360]
            lats = vertices[:, 1]

            # Handle longitude filtering correctly
            if lon1 <= lon2:
                mask = (lons >= lon1) & (lons <= lon2)  # Standard case
            else:
                mask = (lons >= lon1) | (lons <= lon2)  # Crosses dateline case

            filtered_lats = lats[mask]

            # Keep only points south of lat_ref
            filtered_lats = filtered_lats[filtered_lats < lat_ref]

            if len(filtered_lats) > 0:
                # Compute southward deviation as lat_ref - filtered_lats
                deviation = np.max(lat_ref - filtered_lats)  
                max_deviation = max(max_deviation, deviation)

        max_deviation_timeseries.append((time.values, max_deviation))

    return pd.DataFrame(max_deviation_timeseries, columns=["Time", "Max Meridional Deviation"]), contour_levels


def plot_z500_composite(composite_z500, lat_ref, plotdir, lon1, lon2, lat1, lat2, max_meridional_deviation_df, contour_levels, lon1_index, lon2_index):
    titles = ['Composite of Z500 at Min MSLP - {hours} h'.format(hours=hours_shift), 'Composite of Z500 at Max MSLP']
              
    fig, axes = plt.subplots(1, 2, subplot_kw={'projection': ccrs.PlateCarree()}, figsize=(15, 7))

    vmin = composite_z500.min().values
    vmax = composite_z500.max().values

    for ax, time, title, contour_level in zip(axes, composite_z500.valid_time.values, titles, contour_levels):
        ax.set_extent([lon1, lon2, lat1, lat2], crs=ccrs.PlateCarree())
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        im = composite_z500.sel(valid_time=time).plot(ax=ax, transform=ccrs.PlateCarree(), cmap='coolwarm', levels=20, vmin=vmin, vmax=vmax, add_colorbar=False)
        
        # Plot the reference latitude as a thick black line
        ax.plot([lon1, lon2], [lat_ref, lat_ref], color='black', linewidth=2, transform=ccrs.PlateCarree())
        
        # Plot the reference z500 contour as a thick gray line
        contour = composite_z500.sel(valid_time=time).plot.contour(levels=[contour_level], colors='gray', linewidths=2, add_colorbar=False, transform=ccrs.PlateCarree(), ax=ax)
        
        # Plot the lon1 and lon2 index meridians as thick black dashed lines
        ax.plot([lon1_index, lon1_index], [lat1, lat2], color='black', linestyle='--', linewidth=2, transform=ccrs.PlateCarree())
        ax.plot([lon2_index, lon2_index], [lat1, lat2], color='black', linestyle='--', linewidth=2, transform=ccrs.PlateCarree())
        
        ax.set_title(title)
        ax.set_ylabel('z [m]')  # Add z [m] to the y-axis label
        

    # Add a single colorbar at the bottom of the plots
    cbar = fig.colorbar(im, ax=axes, orientation='horizontal', fraction=0.046, pad=0.15)
    cbar.set_label('Geopotential Height (m)')

    # Add text annotations for reference latitude and max meridional displacement
    for ax, time, contour_level in zip(axes, composite_z500.valid_time.values, contour_levels):
        max_deviation = max_meridional_deviation_df[max_meridional_deviation_df["Time"] == time]["Max Meridional Deviation"].values[0]
        textstr = f'Ref Lat: {lat_ref}°\nContour Value: {contour_level:.0f} m\nΔΦ: {max_deviation:.1f}°'
        ax.text(0.5, -0.15, textstr, transform=ax.transAxes, ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.savefig(os.path.join(plotdir, 'composite_z500_vaia&florence_index.png'), bbox_inches='tight')
    print("saved figure at:", os.path.join(plotdir, 'composite_z500_vaia&florence_index.png'))

        
lat_ref = 45  # Reference latitude

lon1_index=-10
lon2_index=5

max_meridional_deviation_df, contour_levels = calculate_max_meridional_deviation(composite_z500, lat_ref=lat_ref, lon1=lon1_index, lon2=lon2_index)
print("max meridional deviation is: ", max_meridional_deviation_df)
plot_z500_composite(composite_z500, lat_ref=lat_ref, plotdir=plotdir, lon1=lon1, lon2=lon2, lat1=lat1, lat2=lat2, max_meridional_deviation_df=max_meridional_deviation_df, contour_levels=contour_levels, lon1_index=lon1_index, lon2_index=lon2_index)



