import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
from scipy.stats import gaussian_kde
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import glob

# this code reads the filtered tracks after the execution of the script pass_trajectories.sh.
# The tracks are then plotted on a map.

var = "psl"
seas = "SON"
model = "EC-Earth3"
expn = "historical" # historical or scenarioMIP

# dir with CMIP6 data

CMIP6_base_dir = "/home/ghinassi/work/track_output/CMIP6"
plotdir_base = f"/home/ghinassi/work/track_plots/total_tracks/CMIP6/Ec-Earth3/{expn}/{var}/{seas}/"

#ERA5 file for bias calculation
era5_stats_file = "/home/ghinassi/work/track_output/ERA5/SON/msl/stats/ff_trs_neg_scl.std_1984-2014_1.nc"

def read_tracks(ERA5_track_dir, filename=None):
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
                    start_time = int(line.split()[-1])
                    continue
                elif line.startswith("POINT_NUM"):
                    num_points = int(line.split()[1])
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
                        continue
                    elif line.startswith("POINT_NUM"):
                        num_points = int(line.split()[1])
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
                        track_id = None
                        track_data = []
    
    return tracks

def plot_track_density(alltracks, plotdir, lat1=None, lat2=None, lon1=None, lon2=None):
    if alltracks:
        all_lon_values, all_lat_values = [], []
        for track_id, track_data in alltracks.items():
            header = track_data["header"]
            data = track_data["data"]
            
            all_lon_values += [(lon + 180) % 360 - 180 for _, lon, _ in data]
            all_lat_values += [lat for _, _, lat in data]

        xy = np.vstack([all_lon_values, all_lat_values])
        kde = gaussian_kde(xy, bw_method=0.1)
        
        lon_grid, lat_grid = np.meshgrid(np.arange(lon1, lon2, 0.05),
                                         np.arange(lat1, lat2, 0.05))
        
        density = kde(np.vstack([lon_grid.ravel(), lat_grid.ravel()])).reshape(lon_grid.shape)

        projection = ccrs.PlateCarree()
        
        fig, ax = plt.subplots(subplot_kw={'projection': projection}, figsize=(10, 6))

        c = ax.pcolormesh(lon_grid, lat_grid, density, shading='auto', cmap='viridis', alpha=0.6, transform=projection)
        
        cbar = plt.colorbar(c, ax=ax, orientation='vertical', pad=0.02, label="Track Density")

        ax.set_xticks(range(-180, 181, 30), crs=projection)
        ax.set_yticks(range(-90, 91, 10), crs=projection)

        if lat1 and lat2 and lon1 and lon2:
            ax.set_extent([lon1, lon2, lat1, lat2], crs=projection)

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

        ax.add_feature(cfeature.LAND, color='lightgrey')

        ax.set_title("Track Density (Var: {} - Seas: {} - Model: {})".format(var, seas, model))
        
        os.makedirs(plotdir, exist_ok=True)
        
        plt.savefig(plotdir + f"trackdensity_{var}_{seas}_{model}_allensm.png")
        print("saved plot named: ", plotdir + f"trackdensity_{var}_{seas}_{model}_allensm.png")
        plt.close()
        

def read_all_ensemble_tracks(base_dir, model, seas, var):
    ensemble_tracks = {}
    ensemble_dirs = glob.glob(os.path.join(base_dir, model, "historical", seas, "*", var, "total_tracks"))
    
    for ensm_dir in ensemble_dirs:
        ensm = os.path.basename(os.path.dirname(os.path.dirname(ensm_dir)))
        print("ensm_dir is: ", ensm_dir)
        concatenated_tracks_filename = f"concatenated_tracks_{ensm}.txt"
        all_tracks = read_tracks(ensm_dir, concatenated_tracks_filename)
        ensemble_tracks[ensm] = {
            "tracks": all_tracks,
        }
    
    return ensemble_tracks

def plot_stats_from_TRACK(stats_file, plotdir, ensm, extent):
    ds = xr.open_dataset(stats_file)

    mstr = ds['mstr']
    tden = ds['tden']
    gden = ds['gden']
    lden = ds['lden']
    
    # Mask mean intensity where track density is less than or equal to 1
    mstr = mstr.where(tden > 1)
    
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
    
    if expn == "historical":
        fig.suptitle(f'EC-Earth3 - {ensm} - stats (1984-2014)', fontsize=16)
        
    elif expn == "scenarioMIP":
        fig.suptitle(f'EC-Earth3 - {ensm} - stats (2070-2100)', fontsize=16)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    os.makedirs(os.path.join(plotdir, ensm, seas, var), exist_ok=True)
    
    plt.savefig(os.path.join(plotdir, ensm, seas, var, f'track_stats_from_TRACK_EC-Earth3_{expn}_{ensm}.png'))
    print(f"saved plot named: {os.path.join(plotdir, ensm, seas, var, f'track_stats_from_TRACK_EC-Earth3_{expn}_{ensm}.png')}")
    plt.close()
    
def plot_ensemble_mean_stats_from_TRACK(stats_files, plotdir_base, seas, var, extent):   
    
    # Initialize lists to store ensemble data
    all_mstr, all_tden, all_gden, all_lden = [], [], [], []

    for stats_file in stats_files:
        ensm = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(stats_file))))
        ds = xr.open_dataset(stats_file)
        all_mstr.append(ds['mstr'])
        all_tden.append(ds['tden'])
        all_gden.append(ds['gden'])
        all_lden.append(ds['lden'])

    # Calculate ensemble mean
    mean_mstr = xr.concat(all_mstr, dim='ensemble').mean(dim='ensemble')
    mean_tden = xr.concat(all_tden, dim='ensemble').mean(dim='ensemble')
    mean_gden = xr.concat(all_gden, dim='ensemble').mean(dim='ensemble')
    mean_lden = xr.concat(all_lden, dim='ensemble').mean(dim='ensemble')

    # Mask mean_mstr where mean_tden <= 1
    mean_mstr = mean_mstr.where(mean_tden > 1)

    # Plot ensemble mean
    fig, axes = plt.subplots(2, 2, subplot_kw={'projection': ccrs.NorthPolarStereo()}, figsize=(15, 10))
    mean_mstr.plot(ax=axes[0, 0], transform=ccrs.PlateCarree(), cmap='Reds', vmin=0, vmax=28, cbar_kwargs={'label': 'Mean Intensity [hPa]', 'shrink': 0.8, 'extend': 'max'})
    axes[0, 0].set_title('Mean Intensity')
    axes[0, 0].coastlines()
    axes[0, 0].set_extent(extent, crs=ccrs.PlateCarree())

    mean_tden.plot(ax=axes[0, 1], transform=ccrs.PlateCarree(), cmap='Reds', vmin=0, vmax=14, cbar_kwargs={'label': 'Track Density', 'shrink': 0.8, 'extend': 'max'})
    axes[0, 1].set_title('Track Density')
    axes[0, 1].coastlines()
    axes[0, 1].set_extent(extent, crs=ccrs.PlateCarree())

    mean_gden.plot(ax=axes[1, 0], transform=ccrs.PlateCarree(), cmap='Reds', vmin=0, vmax=3, cbar_kwargs={'label': 'Genesis Density', 'shrink': 0.8, 'extend': 'max'})
    axes[1, 0].set_title('Genesis Density')
    axes[1, 0].coastlines()
    axes[1, 0].set_extent(extent, crs=ccrs.PlateCarree())

    mean_lden.plot(ax=axes[1, 1], transform=ccrs.PlateCarree(), cmap='Reds', vmin=0, vmax=3, cbar_kwargs={'label': 'Lysis Density', 'shrink': 0.8, 'extend': 'max'})
    axes[1, 1].set_title('Lysis Density')
    axes[1, 1].coastlines()
    axes[1, 1].set_extent(extent, crs=ccrs.PlateCarree())
    
    if expn == "historical":
        fig.suptitle('EC-Earth3 - Ensemble Mean Stats (1984-2014) - SON', fontsize=16)
    elif expn == "scenarioMIP":
        fig.suptitle('EC-Earth3 - Ensemble Mean Stats (2070-2100)- SON', fontsize=16)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    os.makedirs(os.path.join(plotdir_base, 'ensemble_mean', seas, var), exist_ok=True)

    plt.savefig(os.path.join(plotdir_base, 'ensemble_mean', seas, var, f'track_stats_from_TRACK_EC-Earth3_{expn}_{seas}_ensmean.png'))
    print(f"saved plot named: {os.path.join(plotdir_base, 'ensemble_mean', seas, var, f'track_stats_from_TRACK_EC-Earth3_{expn}_{seas}_ensmean.png')}")
    plt.close()
    
def plot_bias(stats_files, stats_files_ref, plotdir_base, seas, var, expn, extent):  
    
    # Initialize lists to store ensemble data
    all_mstr, all_tden, all_gden, all_lden = [], [], [], []

    for stats_file in stats_files:
        ds = xr.open_dataset(stats_file)
        all_mstr.append(ds['mstr'])
        all_tden.append(ds['tden'])
        all_gden.append(ds['gden'])
        all_lden.append(ds['lden'])

    # Calculate ensemble mean
    mean_mstr = xr.concat(all_mstr, dim='ensemble').mean(dim='ensemble')
    mean_tden = xr.concat(all_tden, dim='ensemble').mean(dim='ensemble')
    mean_gden = xr.concat(all_gden, dim='ensemble').mean(dim='ensemble')
    mean_lden = xr.concat(all_lden, dim='ensemble').mean(dim='ensemble')
    
    # Mask mean_mstr where mean_tden <= 1
    mean_mstr = mean_mstr.where(mean_tden > 1)
    
    if expn == "historical":
        era5_ds = xr.open_dataset(stats_files_ref)
        bias_mstr = mean_mstr - era5_ds['mstr']
        bias_tden = mean_tden - era5_ds['tden']
        bias_gden = mean_gden - era5_ds['gden']
        bias_lden = mean_lden - era5_ds['lden']
        contour_data = era5_ds['tden']
    elif expn == "scenarioMIP":
        # Initialize lists to store reference ensemble data
        all_mstr_ref, all_tden_ref, all_gden_ref, all_lden_ref = [], [], [], []

        for stats_file_ref in stats_files_ref:
            ds_ref = xr.open_dataset(stats_file_ref)
            all_mstr_ref.append(ds_ref['mstr'])
            all_tden_ref.append(ds_ref['tden'])
            all_gden_ref.append(ds_ref['gden'])
            all_lden_ref.append(ds_ref['lden'])

        # Calculate reference ensemble mean
        mean_mstr_ref = xr.concat(all_mstr_ref, dim='ensemble').mean(dim='ensemble')
        mean_tden_ref = xr.concat(all_tden_ref, dim='ensemble').mean(dim='ensemble')
        mean_gden_ref = xr.concat(all_gden_ref, dim='ensemble').mean(dim='ensemble')
        mean_lden_ref = xr.concat(all_lden_ref, dim='ensemble').mean(dim='ensemble')
        
        bias_mstr = mean_mstr - mean_mstr_ref
        bias_tden = mean_tden - mean_tden_ref
        bias_gden = mean_gden - mean_gden_ref
        bias_lden = mean_lden - mean_lden_ref
        contour_data = mean_tden_ref

        # Calculate standard deviation for historical ensemble
        std_mstr = xr.concat(all_mstr_ref, dim='ensemble').std(dim='ensemble') 
        std_tden = xr.concat(all_tden_ref, dim='ensemble').std(dim='ensemble') 
        std_gden = xr.concat(all_gden_ref, dim='ensemble').std(dim='ensemble') 
        std_lden = xr.concat(all_lden_ref, dim='ensemble').std(dim='ensemble') 
        
    # Plot ensemble bias
    
    # define regional extent
    fig, axes = plt.subplots(2, 2, subplot_kw={'projection': ccrs.NorthPolarStereo()}, figsize=(15, 10)) 
    bias_mstr.plot(ax=axes[0, 0], transform=ccrs.PlateCarree(), cmap='coolwarm', vmin=-3, vmax=3, cbar_kwargs={'label': 'Difference in Mean Intensity [hPa]', 'shrink': 0.8, 'extend': 'both'})
    axes[0, 0].set_title('Mean Intensity')
    axes[0, 0].coastlines()
    axes[0, 0].set_extent(extent, crs=ccrs.PlateCarree())
    contour_data.plot.contour(ax=axes[0, 0], levels=[8], colors='black', linewidths=1.6, transform=ccrs.PlateCarree())

    bias_tden.plot(ax=axes[0, 1], transform=ccrs.PlateCarree(), cmap='coolwarm', vmin=-2, vmax=2, cbar_kwargs={'label': 'Difference in Track Density', 'shrink': 0.8, 'extend': 'both'})
    axes[0, 1].set_title('Track Density')
    axes[0, 1].coastlines()
    axes[0, 1].set_extent(extent, crs=ccrs.PlateCarree())
    contour_data.plot.contour(ax=axes[0, 1], levels=[8], colors='black', linewidths=1.6, transform=ccrs.PlateCarree())

    bias_gden.plot(ax=axes[1, 0], transform=ccrs.PlateCarree(), cmap='coolwarm', vmin=-0.5, vmax=0.5, cbar_kwargs={'label': 'Difference in Genesis Density', 'shrink': 0.8, 'extend': 'both'})
    axes[1, 0].set_title('Genesis Density')
    axes[1, 0].coastlines()
    axes[1, 0].set_extent(extent, crs=ccrs.PlateCarree())
    contour_data.plot.contour(ax=axes[1, 0], levels=[8], colors='black', linewidths=1.6, transform=ccrs.PlateCarree())

    bias_lden.plot(ax=axes[1, 1], transform=ccrs.PlateCarree(), cmap='coolwarm', vmin=-0.5, vmax=0.5, cbar_kwargs={'label': 'Difference in Lysis Density', 'shrink': 0.8, 'extend': 'both'})
    axes[1, 1].set_title('Lysis Density')
    axes[1, 1].coastlines()
    axes[1, 1].set_extent(extent, crs=ccrs.PlateCarree())
    contour_data.plot.contour(ax=axes[1, 1], levels=[8], colors='black', linewidths=1.6, transform=ccrs.PlateCarree())
    
    if expn == "historical":
        fig.suptitle('EC-Earth3 - Ensemble mean bias (ref: ERA5 (1984-2014)) - SON', fontsize=16)
    elif expn == "scenarioMIP":
        # Add stippling where bias magnitude is greater than one standard error
        stipple_mask_mstr = np.abs(bias_mstr) > std_mstr
        stipple_mask_tden = np.abs(bias_tden) > std_tden
        stipple_mask_gden = np.abs(bias_gden) > std_gden
        stipple_mask_lden = np.abs(bias_lden) > std_lden

        lon, lat = np.meshgrid(bias_mstr.long, bias_mstr.lat)

        axes[0, 0].scatter(lon[stipple_mask_mstr], lat[stipple_mask_mstr], 
                           s=1, color='k', transform=ccrs.PlateCarree(), alpha=0.6)
        axes[0, 1].scatter(lon[stipple_mask_tden], lat[stipple_mask_tden], 
                           s=1, color='k', transform=ccrs.PlateCarree(), alpha=0.6)
        axes[1, 0].scatter(lon[stipple_mask_gden], lat[stipple_mask_gden], 
                           s=1, color='k', transform=ccrs.PlateCarree(), alpha=0.6)
        axes[1, 1].scatter(lon[stipple_mask_lden], lat[stipple_mask_lden], 
                           s=1, color='k', transform=ccrs.PlateCarree(), alpha=0.6)
        
        fig.suptitle('EC-Earth3 - Climate change response: ssp245 (2070-2100) vs historical (1984-2014) - SON', fontsize=14)

    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    os.makedirs(os.path.join(plotdir_base, 'ensemble_bias', seas, var), exist_ok=True)
    
    plt.savefig(os.path.join(plotdir_base, 'ensemble_bias', seas, var, f'EC-Earth3_ensemble_bias_{expn}_{seas}.png'))
    print(f"saved plot named: {os.path.join(plotdir_base, 'ensemble_bias', seas, var, f'EC-Earth3_ensemble_bias_{expn}_{seas}.png')}")
    plt.close()
    
    
    
if __name__ == "__main__":
    
    use_stats_from_TRACK = True
    
    if use_stats_from_TRACK == False:
        all_tracks = {}

        ensemble_tracks = read_all_ensemble_tracks("/home/ghinassi/work/track_output/CMIP6", model, seas, var)

        for ensm, data in ensemble_tracks.items():
            all_tracks = data["tracks"]

            combined_tracks = {}

            for track_id, track_data in data["tracks"].items():
                combined_tracks[f"{ensm}_{track_id}"] = track_data

        plot_track_density(all_tracks, plotdir_base, lat1=30, lat2=48, lon1=-0.1, lon2=25)
        
    elif use_stats_from_TRACK == True:
        
        if expn == "historical":
            stats_dir = f"/home/ghinassi/work/track_output/CMIP6/EC-Earth3/{expn}/{seas}/*/{var}/stats/"
            stats_files = glob.glob(os.path.join(stats_dir, "ff_trs_neg_scl.std_1984-2014_1.nc"))
        elif expn == "scenarioMIP":
            stats_dir = f"/home/ghinassi/work/track_output/CMIP6/EC-Earth3/{expn}/ssp245/{seas}/*/{var}/stats/"
            stats_files = glob.glob(os.path.join(stats_dir, "ff_trs_neg_scl.std_2070-2100_1.nc"))
        else:
            print("No stats files found.")
        
        plot_single_members = False
        plot_ensemble_mean = True
        plot_ens_bias = True
        # Define the extent for the Euro-Atlantic sector in the Northern Hemisphere
        extent = [-90, 40, 25, 100]  # [lon_min, lon_max, lat_min, lat_max]

        if plot_single_members:            
            for stats_file in stats_files:
                ensm = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(stats_file))))
                plot_stats_from_TRACK(stats_file, plotdir_base, ensm, extent)
        if plot_ensemble_mean:
            plot_ensemble_mean_stats_from_TRACK(stats_files, plotdir_base, seas, var, extent)
        if plot_bias:
            if expn=="historical":
                stats_files_ref = era5_stats_file            
                plot_bias(stats_files, stats_files_ref,plotdir_base, seas, var, expn, extent)
            elif expn=="scenarioMIP":
                stats_dir_hist = f"/home/ghinassi/work/track_output/CMIP6/EC-Earth3/historical/{seas}/*/{var}/stats/"
                stats_files_hist = glob.glob(os.path.join(stats_dir_hist, "ff_trs_neg_scl.std_1984-2014_1.nc"))         
                plot_bias(stats_files, stats_files_hist,plotdir_base, seas, var, expn, extent)
        else:
            print("No plots to be generated.")
