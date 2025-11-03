import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

var="tp"
seas="SON"

ERA5_total_tracks_dir="/home/ghinassi/work/track_output/ERA5/SON/msl/total_tracks"
ERA5_track_dir_vaia_analogue = "/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue"
plotdir= "/home/ghinassi/work/track_plot/tp_pdf/"

def read_ERA5_tracks(ERA5_track_dir, filename=None, added_field_tp=False):
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
                    if added_field_tp:
                        data = line.replace('&', ' ').split()
                        date = data[0]
                        lon = float(data[1])
                        lat = float(data[2])
                        mslp = float(data[3])
                        tp = float(data[4])
                        track_data.append((date, lon, lat, mslp, tp))
                    else:
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
                        if added_field_tp:
                            data = line.replace('&', ' ').split()
                            date = data[0]
                            lon = float(data[1])
                            lat = float(data[2])
                            mslp = float(data[3])
                            tp = float(data[4])
                            track_data.append((date, lon, lat, mslp, tp))
                        else:
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
                        track_id = None
                        track_data = []
    
    return tracks

def spatial_filter_tracks(tracks, lon_min, lon_max, lat_min, lat_max, added_field_tp=False):
    filtered_tracks = {}
    
    for track_id in tracks:
        track_data = tracks[track_id]["data"]
        if added_field_tp:
            track_data_filtered = [(date, lon, lat, mslp, tp) for date, lon, lat, mslp, tp in track_data if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max]
        else:
            track_data_filtered = [(date, lon, lat, mslp) for date, lon, lat, mslp in track_data if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max]
        
        if track_data_filtered:
            filtered_tracks[track_id] = {
                "header": tracks[track_id]["header"],
                "data": track_data_filtered
            }
    
    return filtered_tracks

def plot_tp_pdf(tp_tot, tp_filt1, tp_filt2, plotdir, lon_min, lon_max, lat_min, lat_max):
    tp_tot_sum = []
    tp_filt1_sum = []
    
    for track_id, track_data in tp_tot.items():
        data = track_data["data"]
        tp = [tp for _, _, _, _, tp in data]
        tp_tot_sum.append(sum(tp))
        
    for track_id, track_data in tp_filt1.items():
        data = track_data["data"]
        tp = [tp for _, _, _, _, tp in data]
        tp_filt1_sum.append(sum(tp)) 
        

    tp_filt2_sum = []
    for track_id, track_data in tp_filt2.items():
        data = track_data["data"]
        tp = [tp for _, _, _, _, tp in data]
        tp_filt2_sum.append(sum(tp))
        
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.hist(tp_tot_sum, bins=20, density=True, alpha=0.5, label=f"Total tracks (n={len(tp_tot)})")
    ax.hist(tp_filt1_sum, bins=20, density=True, alpha=0.5, label=f"Vaia gen tracks (n={len(tp_filt1)})")
    ax.hist(tp_filt2_sum, bins=20, density=True, alpha=0.5, label=f"Vaia gen+pass tracks (n={len(tp_filt2)})")
    
    mean_tot = np.mean(tp_tot_sum)
    mean_filt1 = np.mean(tp_filt1_sum)
    mean_filt2 = np.mean(tp_filt2_sum)
    
    std_err_tot = np.std(tp_tot_sum) / np.sqrt(len(tp_tot_sum))
    std_err_filt1 = np.std(tp_filt1_sum) / np.sqrt(len(tp_filt1_sum))
    std_err_filt2 = np.std(tp_filt2_sum) / np.sqrt(len(tp_filt2_sum))
    
    ax.axvline(mean_tot, color='blue', linestyle='dashed', linewidth=1)
    ax.axvline(mean_filt1, color='orange', linestyle='dashed', linewidth=1)
    ax.axvline(mean_filt2, color='green', linestyle='dashed', linewidth=1)
    
    ax.text(mean_tot, ax.get_ylim()[1]*0.9, f'Mean: {mean_tot:.2f} ± {std_err_tot:.2f}', color='blue')
    ax.text(mean_filt1, ax.get_ylim()[1]*0.8, f'Mean: {mean_filt1:.2f} ± {std_err_filt1:.2f}', color='orange')
    ax.text(mean_filt2, ax.get_ylim()[1]*0.7, f'Mean: {mean_filt2:.2f} ± {std_err_filt2:.2f}', color='green')
    
    ax.set_title(f"Total Precipitation distribution for tracks between ({lat_min}-{lat_max}°N, {lon_min}-{lon_max}°E) for ERA5")
    ax.set_xlabel("Total Precipitation (mm)")
    ax.set_ylabel("PDF")
    ax.legend()
    
    if not os.path.exists(plotdir):
        os.makedirs(plotdir)
    
    plt.savefig(plotdir+"tp_pdf_vaialike_ERA5.png")
    plt.close()
    print("saved plot in:", plotdir+"tp_pdf_vaialike_ERA5.png")
    

ERA5_total_tracks = read_ERA5_tracks(ERA5_total_tracks_dir, filename="concatenated_tracks.TPrad5.txt", added_field_tp=True)
ERA5_vaiagen_tracks = read_ERA5_tracks(ERA5_track_dir_vaia_analogue, filename="concatenated_tracks_latgen38_longen4_radgen4_ff_trs_neg.TP_rad5.txt", added_field_tp=True)
ERA5_vaiagen_vaiapass_tracks = read_ERA5_tracks(ERA5_track_dir_vaia_analogue, filename="concatenated_tracks_latgen38_longen4_radgen4_latpas45_lonpas8_radpas2_ff_trs_neg.TP_rad5.txt", added_field_tp=True)

lon_min = 0
lon_max = 20
lat_min = 30
lat_max = 48

ERA5_total_tracks = spatial_filter_tracks(ERA5_total_tracks, lon_min, lon_max, lat_min, lat_max, added_field_tp=True)
ERA5_vaiagen_tracks = spatial_filter_tracks(ERA5_vaiagen_tracks, lon_min, lon_max, lat_min, lat_max, added_field_tp=True)
ERA5_vaiagen_vaiapass_tracks = spatial_filter_tracks(ERA5_vaiagen_vaiapass_tracks, lon_min, lon_max, lat_min, lat_max, added_field_tp=True)
plot_tp_pdf(ERA5_total_tracks, ERA5_vaiagen_tracks, ERA5_vaiagen_vaiapass_tracks, plotdir, lon_min, lon_max, lat_min, lat_max)

