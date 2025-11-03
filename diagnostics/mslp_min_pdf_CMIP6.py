import os
import glob
import matplotlib.pyplot as plt
import numpy as np

model = "EC-Earth3"
var = "psl"
seas = "SON"

# dir with the concatenated tracks
CMIP6_total_tracks_dir_pattern = f"/home/ghinassi/work/track_output/CMIP6/{model}/historical/{seas}/*/{var}/total_tracks"

# dir with the vaia-like filtered tracks
CMIP6_track_dir_vaia_analogue_pattern = f"/home/ghinassi/work/track_output/CMIP6/{model}/historical/{seas}/*/{var}/vaia_analogue"

# dir for mslp from ERA5
plotdir = "/home/ghinassi/work/diagnostics/plots/mslp_pdf/"

def read_tracks(track_dir):
    tracks = {}
    for root, _, files in os.walk(track_dir):
        for filename in files:
            track_id = None
            track_data = []
            with open(os.path.join(root, filename), "r") as file:
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
    return tracks

def read_all_tracks(pattern):
    all_tracks = {}
    for track_dir in glob.glob(pattern):
        print("reading tracks from:", track_dir)
        tracks = read_tracks(track_dir)
        all_tracks.update(tracks)
    return all_tracks

def spatial_filter_tracks(tracks, lon_min, lon_max, lat_min, lat_max):
    filtered_tracks = {}
    for track_id in tracks:
        track_data = tracks[track_id]["data"]
        track_data_filtered = [(date, lon, lat, mslp) for date, lon, lat, mslp in track_data if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max]
        if track_data_filtered:
            filtered_tracks[track_id] = {
                "header": tracks[track_id]["header"],
                "data": track_data_filtered
            }
    return filtered_tracks

def plot_mslp_pdf(mslp_tot, mslp_filt, plotdir, lon_min, lon_max, lat_min, lat_max):
    mslp_tot_min = []
    mslp_filt_min = []

    for track_id, track_data in mslp_tot.items():
        data = track_data["data"]
        mslp = [mslp for _, _, _, mslp in data]
        mslp_tot_min.append(max(mslp))

    for track_id, track_data in mslp_filt.items():
        data = track_data["data"]
        mslp = [mslp for _, _, _, mslp in data]
        mslp_filt_min.append(max(mslp))

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.hist(mslp_tot_min, bins=20, density=True, alpha=0.5, label=f"Total tracks (n={len(mslp_tot)})")
    ax.hist(mslp_filt_min, bins=20, density=True, alpha=0.5, label=f"Vaia gen+pass tracks (n={len(mslp_filt)})")

    mean_tot = np.mean(mslp_tot_min)
    mean_filt = np.mean(mslp_filt_min)

    std_err_tot = np.std(mslp_tot_min) / np.sqrt(len(mslp_tot_min))
    std_err_filt = np.std(mslp_filt_min) / np.sqrt(len(mslp_filt_min))

    ax.axvline(mean_tot, linestyle='dashed', linewidth=1)
    ax.axvline(mean_filt, linestyle='dashed', linewidth=1)

    ax.text(mean_tot, ax.get_ylim()[1]*0.9, f'Mean: {mean_tot:.2f} ± {std_err_tot:.2f}')
    ax.text(mean_filt, ax.get_ylim()[1]*0.8, f'Mean: {mean_filt:.2f} ± {std_err_filt:.2f}')

    ax.set_title(f"MSLP anomaly distribution for tracks between ({lat_min}-{lat_max}°N, {lon_min}-{lon_max}°E) for {model}")
    ax.set_xlabel("Max mslp anomaly (hPa)")
    ax.set_ylabel("PDF")
    ax.legend()

    if not os.path.exists(plotdir):
        os.makedirs(plotdir)

    plt.savefig(plotdir+f"mslp_pdf_vaialike_{model}.png")
    plt.close()
    print("saved plot in:", plotdir+f"mslp_pdf_vaialike_{model}.png")

if __name__ == "__main__":
    CMIP6_total_tracks = read_all_tracks(CMIP6_total_tracks_dir_pattern)
    CMIP6_vaiagen_vaiapass_tracks = read_all_tracks(CMIP6_track_dir_vaia_analogue_pattern)

    lon_min = 0
    lon_max = 20
    lat_min = 30
    lat_max = 48

    CMIP6_total_tracks = spatial_filter_tracks(CMIP6_total_tracks, lon_min, lon_max, lat_min, lat_max)
    CMIP6_vaiagen_vaiapass_tracks = spatial_filter_tracks(CMIP6_vaiagen_vaiapass_tracks, lon_min, lon_max, lat_min, lat_max)
    plot_mslp_pdf(CMIP6_total_tracks, CMIP6_vaiagen_vaiapass_tracks, plotdir, lon_min, lon_max, lat_min, lat_max)
