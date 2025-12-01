import xarray as xr
import numpy as np
import pickle
import os
from glob import glob
import pandas as pd

import matplotlib
from cartopy.util import add_cyclic_point
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.feature as cfeature


# ======================================================================================
# ENSEMBLES
# ======================================================================================
ensemble_list = [
    'r2i1p1f1','r7i1p1f1','r10i1p1f1', 'r12i1p1f1','r14i1p1f1',
    'r16i1p1f1','r17i1p1f1','r18i1p1f1','r19i1p1f1','r20i1p1f1','r21i1p1f1',
    'r22i1p1f1','r23i1p1f1','r24i1p1f1','r25i1p1f1'
]


# ======================================================================================
# HELPERS
# ======================================================================================

def filter_single(index_dict, start_year, end_year):
    """Filter ERA5 (single dict: {timestamp: value})."""
    return {
        t: v for t, v in index_dict.items()
        if start_year <= pd.to_datetime(t).year <= end_year
        and v is not None and not np.isnan(v)
    }

def filter_by_year(index_dict, start_year, end_year):
    """Filter CMIP6 (dict of dicts: {ens: {timestamp: value}})."""
    filtered = {}
    for ens, ts_dict in index_dict.items():
        filtered[ens] = {
            t: v
            for t, v in ts_dict.items()
            if start_year <= pd.to_datetime(t).year <= end_year
            and v is not None and not np.isnan(v)
        }
    return filtered


def composite_z500(z500_dir, timestamps, varname="z", time_var="time", level=None):
    """Load z500 files in a directory & compute composite mean for matching timestamps."""
    files = sorted(glob(os.path.join(z500_dir, "*.nc")))
    if not files:
        print(f"No NetCDF files in {z500_dir}")
        return None

    ds = xr.open_mfdataset(files, combine="by_coords")

    # match timestamps
    ds_times = pd.to_datetime(ds[time_var].values)
    sel_times = [pd.to_datetime(t) for t in timestamps if pd.to_datetime(t) in ds_times]

    if len(sel_times) == 0:
        print(f"No matching timestamps in {z500_dir}")
        return None

    comp = ds[varname].sel({time_var: sel_times}).mean(dim=time_var)

    if level is not None and "plev" in comp.dims:
        comp = comp.sel(plev=level)

    # convert geopotential in geopotential height (m) only if varname is "z" (ERA5 )
    if varname=="z":
        comp = comp / 9.81
    if "latitude" in comp.dims and "longitude" in comp.dims:
        comp = comp.rename({"latitude": "lat", "longitude": "lon"})

    return comp


def plot_composite(field, title, plotname, plotdir, lat_bounds, lon_bounds):
    """
    Plot a composite z500 (or anomaly) field.
    Ensures field is 2D (lat, lon), adds cyclic point, and plots contours + shading.
    """

    # -----------------------------------------------------------
    # 1) FORCE FIELD TO BE 2D: average out any non-lat/lon dims
    # -----------------------------------------------------------
    for d in field.dims:
        if d not in ("lat", "lon"):
            field = field.mean(d)

    # Now guaranteed shape = (lat, lon)

    # -----------------------------------------------------------
    # 2) Compute anomaly
    # -----------------------------------------------------------
    field_anom = field - field.mean(dim=("lat", "lon"))

    # -----------------------------------------------------------
    # 3) Determine longitude axis index
    # -----------------------------------------------------------
    lon_dim = field_anom.dims.index("lon")

    # -----------------------------------------------------------
    # 4) Add cyclic point for contouring
    # -----------------------------------------------------------
    field_cyc, lon_cyc = add_cyclic_point(
        field_anom.values,
        coord=field_anom.lon.values,
        axis=lon_dim
    )

    # -----------------------------------------------------------
    # 5) Start plotting
    # -----------------------------------------------------------
    plt.figure(figsize=(8, 5))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # ---- SHADING: original field (non-anomalous) ----
    im = field.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap="RdYlBu_r",
        vmin=5200, vmax=6000,
        add_colorbar=False
    )

    # ---- CONTOURS: anomaly ----
    levels = np.arange(-200, 201, 40)

    ax.contour(
        lon_cyc,
        field.lat.values,
        field_cyc,
        levels=levels,
        colors="black",
        linewidths=1,
        transform=ccrs.PlateCarree()
    )

    # -----------------------------------------------------------
    # 6) Map features
    # -----------------------------------------------------------
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.set_extent([lon_bounds[0], lon_bounds[1],
                   lat_bounds[0], lat_bounds[1]],
                  crs=ccrs.PlateCarree())

    gl = ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False

    cbar = plt.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Geopotential height (m)")

    plt.title(title)

    # -----------------------------------------------------------
    # 7) Save
    # -----------------------------------------------------------
    outfile = os.path.join(plotdir, f"{plotname}.png")
    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {outfile}")



# ======================================================================================
# MAIN PROGRAM
# ======================================================================================

def main():

    # ====================== YEAR RANGES ======================
    ERA5_RANGE = (1984, 2014)
    HIST_RANGE = (1984, 2014)
    SSP245_RANGE = (2070, 2100)
    threshold = 0.9

    # ====================== DIRECTORIES ======================
    z500_index_pkl = "/home/ghinassi/work/similarity_pattern_index_pkl"

    ERA5_z500_dir = (
        "/home/ghinassi/nas_zappa/naszappa/ghinassi/ERA5/"
        "z500/grid_1x1/SON/"
    )

    CMIP6_hist_base = (
        "/home/ghinassi/nas_zappa/naszappa/ghinassi/output/CMIP6/"
        "historical/EC-Earth3/6hrPt/atmos/6hrPlevPt/{ens}/zg500/SON/"
    )

    CMIP6_ssp245_base = (
        "/home/ghinassi/nas_zappa/naszappa/ghinassi/output/CMIP6/"
        "scenarioMIP/EC-Earth3/ssp245/6hrPt/atmos/6hrPlevPt/{ens}/zg500/SON/"
    )

    plotdir = "/home/ghinassi/work/track_plots/z500_index/"
    os.makedirs(plotdir, exist_ok=True)

    # ==================================================================================
    # LOAD INDEXES
    # ==================================================================================

    # ----- ERA5 -----
    with open(f"{z500_index_pkl}/index_pattern_ERA5.pkl", "rb") as f:
        era5_index = pickle.load(f)

    # ----- CMIP6 HISTORICAL & SSP245 (PKL per ensemble) -----
    hist_index = {}
    ssp245_index = {}

    for ens in ensemble_list:

        hist_file = f"{z500_index_pkl}/index_pattern_EC-Earth3_historical_{ens}.pkl"
        ssp245_file = f"{z500_index_pkl}/index_pattern_EC-Earth3_scenarioMIP_ssp245_{ens}.pkl"

        if os.path.exists(hist_file):
            with open(hist_file, "rb") as f:
                hist_index[ens] = pickle.load(f)
        else:
            print(f"⚠️ Missing historical file: {hist_file}")

        if os.path.exists(ssp245_file):
            with open(ssp245_file, "rb") as f:
                ssp245_index[ens] = pickle.load(f)
        else:
            print(f"⚠️ Missing SSP245 file: {ssp245_file}")


    # ==================================================================================
    # FILTER BY YEAR
    # ==================================================================================

    era5_filt = filter_single(era5_index, *ERA5_RANGE)
    hist_filt = filter_by_year(hist_index, *HIST_RANGE)
    ssp245_filt = filter_by_year(ssp245_index, *SSP245_RANGE)

    era5_ts = [t for t,v in era5_filt.items() if v > threshold]
    hist_ts = {ens:[t for t,v in ts.items() if v>threshold] for ens,ts in hist_filt.items()}
    ssp245_ts = {ens:[t for t,v in ts.items() if v>threshold] for ens,ts in ssp245_filt.items()}


    # ==================================================================================
    # COMPOSITES
    # ==================================================================================

    # ----- ERA5 -----
    print("\nComputing ERA5 composite...")
    era5_comp = composite_z500(ERA5_z500_dir, era5_ts, varname="z", time_var="valid_time")

    # ----- HISTORICAL (ALL MEMBERS) -----
    print("\nComputing Historical multi-ensemble composite...")
    hist_comps = []
    for ens in ensemble_list:
        ts = hist_ts.get(ens, [])
        if len(ts) == 0:
            print(f"⚠️ No timestamps above threshold for {ens}")
            continue

        d = CMIP6_hist_base.format(ens=ens)
        comp = composite_z500(d, ts, varname="zg500")

        if comp is not None:
            hist_comps.append(comp)

    hist_comp_all = xr.concat(hist_comps, dim="ens").mean("ens")


    # ----- SSP245 (ALL MEMBERS) -----
    print("\nComputing SSP245 multi-ensemble composite...")
    scen_comps = []
    for ens in ensemble_list:
        ts = ssp245_ts.get(ens, [])
        if len(ts)==0:
            print(f"⚠️ No timestamps above threshold for {ens}")
            continue

        d = CMIP6_ssp245_base.format(ens=ens)
        comp = composite_z500(d, ts, varname="zg500")

        if comp is not None:
            scen_comps.append(comp)

    ssp245_comp_all = xr.concat(scen_comps, dim="ens").mean("ens")


    # ==================================================================================
    # PLOTS
    # ==================================================================================
    lat_bounds = (30, 60)
    lon_bounds = (-15, 25)

    plot_composite(
        era5_comp, "ERA5 Z500", "ERA5_z500_composite",
        plotdir, lat_bounds, lon_bounds
    )

    plot_composite(
        hist_comp_all, "EC-Earth3 Historical (all ensembles)", "Historical_AllMembers_z500",
        plotdir, lat_bounds, lon_bounds
    )

    plot_composite(
        ssp245_comp_all, "EC-Earth3 SSP245 (all ensembles)", "SSP245_AllMembers_z500",
        plotdir, lat_bounds, lon_bounds
    )


if __name__ == "__main__":
    main()

