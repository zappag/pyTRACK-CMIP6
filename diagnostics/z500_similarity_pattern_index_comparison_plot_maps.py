import xarray as xr
import numpy as np
import pickle
import os
from glob import glob
import pandas as pd  # For datetime parsing

import matplotlib
from cartopy.util import add_cyclic_point
matplotlib.use('Agg')  # must come before importing pyplot
import matplotlib.pyplot as plt


import cartopy.crs as ccrs
import cartopy.feature as cfeature


def filter_by_year_ERA5(index_dict, start_year, end_year):
    return {
        k: v for k, v in index_dict.items()
        if start_year <= pd.to_datetime(k).year <= end_year
        and v is not None and not np.isnan(v)
    }

def filter_by_year(index_dict, start_year, end_year):
    filtered_dict = {}
    for ens_member, time_dict in index_dict.items():
        filtered_dict[ens_member] = {
            timestamp: value
            for timestamp, value in time_dict.items()
            if start_year <= pd.to_datetime(timestamp).year <= end_year
            and value is not None and not np.isnan(value)
        }
    return filtered_dict

def main():
    # === Predefined year ranges ===
    ERA5_RANGE = (1984, 2014)
    HIST_RANGE = (1984, 2014)
    SSP245_RANGE = (2070, 2100)
    threshold = 0.9

    z500_index_pkl = "/home/ghinassi/work/similarity_pattern_index_pkl"
    z500_index_ERA5_pkl_filename = "index_pattern_ERA5.pkl"
    z500_index_CMIP6_hist_pkl_filename = "index_pattern_EC-Earth3_historical_r10i1p1f1.pkl"
    z500_index_CMIP6_scen_filename = "index_pattern_EC-Earth3_scenarioMIP_ssp245_r10i1p1f1.pkl"

    ERA5_z500_dir = "/home/ghinassi/work_big/ERA5/z500/grid_1x1/SON/"
    CMIP6_hist_z500_dir = "/home/ghinassi/work_big/output/CMIP6/historical/EC-Earth3/6hrPt/atmos/6hrPlevPt/r10i1p1f1/zg500/SON/"
    CMIP6_ssp245_z500_dir = "/home/ghinassi/work_big/output/CMIP6/scenarioMIP/EC-Earth3/ssp245//6hrPt/atmos/6hrPlevPt/r10i1p1f1/zg500/SON/"

    #plot directory
    plotdir= "/home/ghinassi/work/track_plots/z500_index/"
    os.makedirs(plotdir, exist_ok=True)
    era5_path = os.path.join(z500_index_pkl, z500_index_ERA5_pkl_filename)
    hist_path = os.path.join(z500_index_pkl, z500_index_CMIP6_hist_pkl_filename)
    ssp245_path = os.path.join(z500_index_pkl, z500_index_CMIP6_scen_filename)

    with open(era5_path, 'rb') as f:
        era5_index = pickle.load(f)
    with open(hist_path, 'rb') as f:
        hist_index = pickle.load(f)
    with open(ssp245_path, 'rb') as f:
        ssp245_index = pickle.load(f)

    era5_filtered = filter_by_year_ERA5(era5_index, *ERA5_RANGE)
    hist_filtered = filter_by_year_ERA5(hist_index, *HIST_RANGE)
    ssp245_filtered = filter_by_year_ERA5(ssp245_index, *SSP245_RANGE)

    era5_timestamps = [k for k, v in era5_filtered.items() if v > threshold]
    hist_timestamps = [k for k, v in hist_filtered.items() if v > threshold]
    ssp245_timestamps = [k for k, v in ssp245_filtered.items() if v > threshold]
  
    """
    print(f"ERA5: {len(era5_timestamps)} timestamps above threshold {threshold}")
    print(f"CMIP6 Historical: {len(hist_timestamps)} timestamps above threshold {threshold}")
    print(f"CMIP6 SSP245: {len(ssp245_timestamps)} timestamps above threshold {threshold}")

    #print such time stamps and the index value for debugging
    print("ERA5 timestamps and index values above threshold:")
    for ts in era5_timestamps:
        print(f"{ts}: {era5_filtered[ts]}") 
        
  
    print("CMIP6 Historical timestamps and index values above threshold for member r10i1p1f1:")
    for ts in hist_timestamps:
        print(f"{ts}: {hist_filtered[ts]}")
        
    print("CMIP6 SSP245 timestamps and index values above threshold for member r10i1p1f1:")
    for ts in ssp245_timestamps:
        print(f"{ts}: {ssp245_filtered[ts]}")
    """
    
    # === Helper function to load and composite z500 data ===
    def composite_z500(z500_dir, timestamps, varname="z", level=None, time_var="time"):
        """
        Compute composite mean of z500 field at given timestamps.
        - z500_dir: directory with z500 files (e.g., ERA5 or CMIP6)
        - timestamps: list of timestamps (strings or datetimes)
        - time_var: name of the time variable in the dataset ("time" or "valid_time")
        """
        # Collect matching files
        files = sorted(glob(os.path.join(z500_dir, "*.nc")))
        if not files:
            raise FileNotFoundError(f"No NetCDF files found in {z500_dir}")

        ds = xr.open_mfdataset(files, combine="by_coords")

        # Attempt to select by time, handling both datetime64 and string formats
        time_index = pd.to_datetime(ds[time_var].values)
        sel_times = [pd.to_datetime(t) for t in timestamps if pd.to_datetime(t) in time_index]

        if not sel_times:
            print(f"⚠️ No matching timestamps found in {z500_dir}")
            return None

        # Select data and compute composite mean
        comp = ds[varname].sel({time_var: sel_times}).mean(dim=time_var)

        if level is not None and "plev" in ds[varname].dims:
            comp = comp.sel(plev=level)

        # If varname is "z", convert geopotential to geopotential height
        if varname == "z":
            g = 9.81  # gravitational acceleration (m/s^2)
            comp = comp / g
            #then rename lat and lon and time to standard names
            comp = comp.rename({"latitude": "lat", "longitude": "lon"})

        return comp

    # === Compute composites ===
    print("Computing composite means for z500 fields...")

    era5_comp = composite_z500(ERA5_z500_dir, era5_timestamps, varname="z", time_var="valid_time")
    hist_comp = composite_z500(CMIP6_hist_z500_dir, hist_timestamps, varname="zg500")
    ssp245_comp = composite_z500(CMIP6_ssp245_z500_dir, ssp245_timestamps, varname="zg500")

    # === Plot maps ===
    def plot_composite(field, title, plotname, lat_bounds=(30, 60), lon_bounds=(-15, 25)):
        """
        Plot the composite mean Z500 field with filled color shading (absolute values)
        and black contour lines showing geopotential height anomalies (deviation from areal mean).
        """
        plt.figure(figsize=(8, 5))
        ax = plt.axes(projection=ccrs.PlateCarree())

        # --- Compute the anomaly (subtract areal mean) ---
        field_anom = field.squeeze() - field.mean(dim=["lat", "lon"]).squeeze()

        # --- Plot color shading of absolute geopotential height ---
        im = field.plot(
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
        field_cyclic, lon_cyclic = add_cyclic_point(field_anom, coord=field.lon, axis=1)

        contours = ax.contour(
            lon_cyclic,
            field.lat,
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
        print(f"Saved plot with anomaly contours: {outfile}")


    #select lat lon box:
    lon1=-15
    lon2=25
    lat1=60
    lat2=30

    plot_composite(era5_comp, "ERA5 z500 Composite (Index > Threshold)", "ERA5_z500_composite", lat_bounds=(lat2, lat1), lon_bounds=(lon1, lon2))
    plot_composite(hist_comp, "EC-Earth3 Historical z500 Composite (Index > Threshold)", "EC-Earth3_Historical_z500_composite", lat_bounds=(lat2, lat1), lon_bounds=(lon1, lon2))
    plot_composite(ssp245_comp, "EC-Earth3 SSP245 z500 Composite (Index > Threshold)", "EC-Earth3_SSP245_z500_composite", lat_bounds=(lat2, lat1), lon_bounds=(lon1, lon2))

    
if __name__ == "__main__":
    main()
