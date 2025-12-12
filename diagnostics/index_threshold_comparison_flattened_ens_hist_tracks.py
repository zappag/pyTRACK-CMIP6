import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sys
from matplotlib.patches import Patch
import scipy.stats as st
import logging
from scipy.stats import gaussian_kde
import os

# === Logger class ===
class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

# === Configuration ===
threshold = 0.9
delta_time = 48  # hours
perform_daily_mean = True

# Set up logging
logging.basicConfig(level=logging.WARNING, format='%(message)s')
logger = logging.getLogger()

# Independent year ranges for datasets
start_year_ERA5 = 1984
end_year_ERA5 = 2014

start_year_hist = 1984
end_year_hist = 2014

start_year_scen = 2070
end_year_scen = 2100

model_name = "EC-Earth3"

# === Paths ===
#ERA5 paths
index_path_ERA5 = "/home/ghinassi/work/similarity_pattern_index_pkl/index_pattern_ERA5.pkl"
ERA5_tracks_path = "/home/ghinassi/work/track_output/ERA5/SON/msl/total_tracks/"
ERA5_filtered_path = "/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue/"
ERA5_filtered_file = "concatenated_tracks_firstlatpass39_firstlonpass4_firstrad3.5_secondlatpass45_secondlonpass10_secondrad3.5_box_1940-2024.txt"

#CMIP6 paths
base_index_path = "/home/ghinassi/work/similarity_pattern_index_pkl/"
base_tracks_path = f"/home/ghinassi/work/track_output/CMIP6/{model_name}/"
vaia_tracks_filename_hist = f"concatenated_tracks_firstlatpass39_firstlonpass4_firstrad3.5_secondlatpass45_secondlonpass10_secondrad3.5_gen_{start_year_hist}-{end_year_hist}.txt"
vaia_tracks_filename_scen = f"concatenated_tracks_firstlatpass39_firstlonpass4_firstrad3.5_secondlatpass45_secondlonpass10_secondrad3.5_gen_{start_year_scen}-{end_year_scen}.txt"

#directory for plotting
plot_dir = "/home/ghinassi/work/track_plots/mslp_pdf/"
if not os.path.exists(plot_dir):
    os.makedirs(plot_dir, exist_ok=True)

ens_list_hist = [
    "r2i1p1f1", "r7i1p1f1", "r10i1p1f1", "r12i1p1f1", "r14i1p1f1",
    "r16i1p1f1", "r17i1p1f1", "r18i1p1f1", "r19i1p1f1", "r20i1p1f1",
    "r21i1p1f1", "r22i1p1f1", "r23i1p1f1", "r24i1p1f1", "r25i1p1f1"
]
ens_list_scen = [
    "r2i1p1f1", "r7i1p1f1", "r10i1p1f1", "r12i1p1f1", "r14i1p1f1",
    "r16i1p1f1", "r17i1p1f1", "r18i1p1f1", "r19i1p1f1", "r20i1p1f1",
    "r21i1p1f1", "r22i1p1f1", "r23i1p1f1", "r24i1p1f1", "r25i1p1f1"
]

def convert_lon(lon):
    return lon - 360 if lon > 180 else lon

def read_index(path):
    return pickle.load(open(path, 'rb'))

def process_index(index_data, start_year=None, end_year=None, daily_mean=True):
    df = pd.DataFrame(list(index_data.items()), columns=['timestamp', 'index_value'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    if start_year and end_year:
        df = df[(df['timestamp'].dt.year >= start_year) & (df['timestamp'].dt.year <= end_year)]

    if daily_mean:
        # Group by date (year-month-day), then average manually — only for dates that exist
        df['date'] = df['timestamp'].dt.floor('D')
        df = df.groupby('date')['index_value'].mean().reset_index()
        df.rename(columns={'date': 'timestamp'}, inplace=True)
    return df


def timestamps_above_threshold(index_path, threshold=0.9, start_year=None, end_year=None):
    df = process_index(read_index(index_path), start_year, end_year, daily_mean=perform_daily_mean)
    return [(row.timestamp.strftime('%Y%m%d%H'), row.index_value) 
        for row in df.itertuples(index=False) if row.index_value > threshold]


def all_timestamps(index_path, start_year=None, end_year=None):
    df = process_index(read_index(index_path), start_year, end_year, daily_mean=perform_daily_mean)
    return [(row.timestamp.strftime('%Y%m%d%H'), row.index_value) 
        for row in df.itertuples(index=False) if not pd.isna(row.index_value)]


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
                        track_id = None
                        track_data = []
    return tracks

def filter_tracks_by_timestamps(tracks, timestamps, delta_time=0):
    ts_set = set()
    for ts, _ in timestamps:
        base = datetime.strptime(ts, '%Y%m%d%H')
        ts_set.add(ts)
        if delta_time > 0:
            ts_set.add((base + pd.Timedelta(hours=delta_time)).strftime('%Y%m%d%H'))
    return {k: v for k, v in tracks.items() if any(p[0] in ts_set for p in v["data"])}

# === ERA5 Analysis ===

timestamps_ERA5 = timestamps_above_threshold(index_path_ERA5, threshold, start_year_ERA5, end_year_ERA5)
all_ts_ERA5 = all_timestamps(index_path_ERA5, start_year_ERA5, end_year_ERA5)
tracks_ERA5 = read_tracks(ERA5_tracks_path, "concatenated_tracks.txt")
vaia_tracks_ERA5 = read_tracks(ERA5_filtered_path, ERA5_filtered_file)

filtered_ERA5 = filter_tracks_by_timestamps(tracks_ERA5, timestamps_ERA5, delta_time)
filtered_vaia_ERA5 = filter_tracks_by_timestamps(vaia_tracks_ERA5, timestamps_ERA5, delta_time)

#prob_pattern_ERA5 = len(timestamps_ERA5) / len(all_ts_ERA5)
#prob_storm_given_pattern_ERA5 = len(filtered_vaia_ERA5) / len(timestamps_ERA5)




# === EC-Earth3 Flattened Ensemble Analysis ===

def analyze_ec_earth_flat(expn, expt, ens_list, start_year, end_year):
    """Compute P(pattern) and P(storm|pattern) for the flattened ensemble (merged members)."""
    label = f"{expn}_{expt}" if expn == "scenarioMIP" else expn
    label_path = f"{expn}/{expt}" if expn == "scenarioMIP" else expn

    all_timestamps_flat = []
    timestamps_above_flat = []
    filtered_vaia_flat = []
    filtered_vaia_counts = {}

    # store per-ensemble counts / lists so we can log them correctly later
    timestamps_above_per_ens = {}
    all_timestamps_per_ens = {}

    for ens in ens_list:
        index_file = os.path.join(base_index_path, f"index_pattern_{model_name}_{label}_{ens}.pkl")
        ts_above = timestamps_above_threshold(index_file, threshold, start_year, end_year)
        ts_all = all_timestamps(index_file, start_year, end_year)

        # keep per-ensemble lists
        timestamps_above_per_ens[ens] = ts_above
        all_timestamps_per_ens[ens] = ts_all

        # extend flattened lists
        all_timestamps_flat.extend(ts_all)
        timestamps_above_flat.extend(ts_above)

        # read storm tracks
        vaia_dir = os.path.join(base_tracks_path, label_path, "SON", ens, "psl/vaia_analogue")
        vaia_tracks = read_tracks(vaia_dir, vaia_tracks_filename_hist if expn == "historical" else vaia_tracks_filename_scen)

        filtered_vaia = filter_tracks_by_timestamps(vaia_tracks, ts_above, delta_time)
        # filtered_vaia is (apparently) a dict of tracks -> keep its values for flattened list
        filtered_vaia_flat.extend(filtered_vaia.values())
        filtered_vaia_counts[ens] = len(filtered_vaia)

    # compute flattened probabilities
    p_pattern = len(timestamps_above_flat) / len(all_timestamps_flat) if all_timestamps_flat else 0
    p_storm = len(filtered_vaia_flat) / len(timestamps_above_flat) if timestamps_above_flat else 0

    logger.info(f"\n=== {model_name} {label} (flattened ensemble) ===")
    logger.info(f"Start year: {start_year}, End year: {end_year}")
    logger.info(f"Total timestamps (flattened): {len(all_timestamps_flat)}")
    logger.info(f"Timestamps above threshold (flattened): {len(timestamps_above_flat)}")
    logger.info(f"Filtered VAIAlike tracks (flattened): {len(filtered_vaia_flat)}")
    logger.info(f"P(pattern): {p_pattern:.3f}")
    logger.info(f"P(storm | pattern): {p_storm:.3f}")

    logger.info("Number of timesteps above threshold and filtered VAIAlike tracks per ensemble:")
    total_ts = 0
    for ens in ens_list:
        # ts_above is the per-ensemble list we stored
        ts_above = timestamps_above_per_ens.get(ens, [])
        count_ts = len(ts_above)
        filtered_count = filtered_vaia_counts.get(ens, 0)
        logger.info(f"  {ens}: {count_ts} timesteps above threshold")
        total_ts += count_ts
    logger.info(f"Total timesteps above threshold summing all ensembles: {total_ts}")
    logger.info(f"Total timesteps from the flattened ens: {len(timestamps_above_flat)}")

    logger.info("\nFiltered VAIAlike track counts per ensemble:")
    total_tracks = 0
    for ens, count in filtered_vaia_counts.items():
        logger.info(f"  {ens}: {count}")
        total_tracks += count
    logger.info(f"Total filtered VAIAlike tracks across all ensembles: {total_tracks}")
    logger.info("Filtered VAIAlike tracks from the flattened ensemble: %d", len(filtered_vaia_flat))

    return p_pattern, p_storm

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



# Flattened historical and scenario results
#prob_pattern_hist, prob_storm_hist = analyze_ec_earth_flat("historical", "", ens_list_hist, start_year_hist, end_year_hist)
#prob_pattern_scen, prob_storm_scen = analyze_ec_earth_flat("scenarioMIP", "ssp245", ens_list_scen, start_year_scen, end_year_scen)

# =====================================================================
# === HISTOGRAM OF MSLP ANOMALIES FOR ERA5, HISTORICAL, SSP245 ========
# =====================================================================

def extract_mslp_anomalies(tracks):
    """Return list of minimum MSLP anomalies per track."""
    anomalies = []
    for track in tracks.values():
        mslp_vals = [p[3] for p in track["data"]]   # p = (time, lon, lat, mslp)
        mslp_anom = np.max(mslp_vals)
        anomalies.append(mslp_anom)
    return anomalies


era5_large_anom = extract_mslp_anomalies(filtered_vaia_ERA5)

#now print the max anomaly of the era5 large anomalies for checking
logger.info(f"Max MSLP anomaly for ERA5 vaia/florence like tracks with large scale precursor: {era5_large_anom} hPa")


# === EC-Earth3 flattened anomalies (historical + scenario) ==========


def collect_flattened_anomalies(expn, expt, ens_list, start_year, end_year):
    all_anom = []
    large_anom = []

    label_path = f"{expn}/{expt}" if expn == "scenarioMIP" else expn

    for ens in ens_list:
        # read all tracks
        all_dir = os.path.join(base_tracks_path, label_path, "SON", ens, "psl/total_tracks")
        all_tracks = read_tracks(all_dir, f"concatenated_tracks_{ens}.txt")
        # read analogue tracks
        vaia_dir = os.path.join(base_tracks_path, label_path, "SON", ens, "psl/vaia_analogue")

        if expn == "historical":
            vaia_file = vaia_tracks_filename_hist
        else:
            vaia_file = vaia_tracks_filename_scen

        vaia_tracks = read_tracks(vaia_dir, vaia_file)
        # read index timestamps
        index_file = os.path.join(base_index_path, f"index_pattern_{model_name}_{expn if expn!='scenarioMIP' else f'{expn}_{expt}'}_{ens}.pkl")
        ts_above = timestamps_above_threshold(index_file, threshold, start_year, end_year)

        # filter both sets
        large_tracks = filter_tracks_by_timestamps(vaia_tracks, ts_above, delta_time)

        # mslp anomalies
        large_anom.extend(extract_mslp_anomalies(large_tracks))

    return np.array(all_anom), np.array(large_anom)


hist_all_anom, hist_large_anom = collect_flattened_anomalies(
    "historical", "", ens_list_hist, start_year_hist, end_year_hist)

scen_all_anom, scen_large_anom = collect_flattened_anomalies(
    "scenarioMIP", "ssp245", ens_list_scen, start_year_scen, end_year_scen)

#print values of max mslp anomalies of the flattened hist and ssp ens for checking
logger.info(f"Number of Historical vaia/florence like tracks with large scale precursor: {len(hist_large_anom)}")
logger.info(f"Max MSLP anomaly for Historical vaia/florence like tracks with large scale precursor: {hist_large_anom} hPa")
logger.info(f"Number of SSP245 vaia/florence like tracks with large scale precursor: {len(scen_large_anom)}")
logger.info(f"Max MSLP anomaly for SSP245 vaia/florence like tracks with large scale precursor: {scen_large_anom} hPa")


def plot_mslp_anomaly_histograms(era5_large_anom, hist_large_anom, scen_large_anom, plot_dir):
    """Plot and save normalized histograms of MSLP anomalies for ERA5, Historical, and SSP245 for double pass tracks above threshold"""
    plt.figure(figsize=(14, 10))

    bins = np.linspace(0, 50, 20)  # adjust depending on your anomaly range


    plt.plot()
    
    #plt.hist(era5_large_anom, bins=bins, alpha=0.5, label="ERA5 – Double pass tracks with large scale", density=True)
    plt.hist(hist_large_anom, bins=bins, alpha=0.5, label="Historical – Double pass tracks with large scale", density=True)
    plt.hist(scen_large_anom, bins=bins, alpha=0.5, label="SSP245 – Double pass tracks with large scale", density=True)
    plt.xlabel("Max MSLP Anomaly (hPa)", fontsize=14)
    plt.ylabel("Normalized Frequency", fontsize=14)
    plt.title("Normalized Histograms of MSLP Anomalies for Double Pass Tracks Above Threshold", fontsize=16)
    plt.legend(fontsize=12) 
    
    plt.tight_layout()
    output_path = os.path.join(plot_dir, "mslp_anomaly_histograms_normalized.png")
    plt.savefig(output_path, dpi=300)
    plt.close()

    print("Normalized histogram saved:", output_path)
    
def plot_mslp_anomaly_pdfs(hist_large_anom, scen_large_anom, plot_dir):
    """Plot and save kernel-smoothed PDFs of MSLP anomalies for ERA5, Historical, and SSP245,
       scaled by number of tracks (i.e., not normalized).
    """

    plt.figure(figsize=(12, 8))

    # Common evaluation grid
    xmin = 0
    xmax = 50
    x_eval = np.linspace(xmin, xmax, 200)

    # Track counts
    n_hist = len(hist_large_anom)
    n_scen = len(scen_large_anom)

    # KDEs with a smaller bandwidth for sharper curves
    kde_hist = gaussian_kde(hist_large_anom, bw_method=0.4)
    kde_scen = gaussian_kde(scen_large_anom, bw_method=0.4)

    # Means and standard deviations
    hist_mean = np.mean(hist_large_anom)
    hist_std = np.std(hist_large_anom)
    scen_mean = np.mean(scen_large_anom)
    scen_std = np.std(scen_large_anom)

    # ----- Scaled KDE Curves -----
    y_hist = kde_hist(x_eval) * n_hist
    y_scen = kde_scen(x_eval) * n_scen

    # Plot KDE curves
    plt.plot(x_eval, y_hist, label=f"Ec-Earth3 Historical ", linewidth=2)
    plt.plot(x_eval, y_scen, label=f"Ec-Earth3 SSP245 ", linewidth=2)

    # ----- Vertical lines for means -----
    plt.axvline(hist_mean, color='blue', linestyle='--')
    plt.axvline(scen_mean, color='orange', linestyle='--')

    # Axis labels
    plt.xlabel("Max MSLP Anomaly (hPa)", fontsize=18)
    plt.ylabel("Storms/tracks Counts", fontsize=18)
    plt.title("PDFs of MSLP Anomalies", fontsize=20)
    # add horizontal and vertical gridlines
    plt.grid(axis='x', color='lightgray', linestyle='--', linewidth=0.5)
    plt.grid(axis='y', color='lightgray', linestyle='--', linewidth=0.5)
    
    #increase width of y andx ticks
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    # Legend for curves
    plot_legend = plt.legend(fontsize=16, loc='upper left')
    plt.gca().add_artist(plot_legend)

    # Legend for vertical lines
    plt.legend(
        handles=[
            plt.Line2D([0], [0], color='blue', linestyle='--',
                       label=f'Historical Mean: {hist_mean:.2f} hPa\nStd Dev: {hist_std:.2f} hPa'),
            plt.Line2D([0], [0], color='orange', linestyle='--',
                       label=f'SSP245 Mean: {scen_mean:.2f} hPa\nStd Dev: {scen_std:.2f} hPa')
        ],
        fontsize=16,
        loc='upper right'
    )

    plt.tight_layout()

    # Save figure
    output_path = os.path.join(plot_dir, "mslp_anomaly_pdfs_scaled_counts.png")
    plt.savefig(output_path, dpi=300)
    plt.close()

    print("Smoothed PDF saved:", output_path)



plot_histogram = True
plot_pdf = True

# Call the function for plotting histograms
if plot_histogram:
    plot_mslp_anomaly_histograms(
        era5_large_anom,
        hist_large_anom,
        scen_large_anom,
        plot_dir
    )
if plot_pdf:
    plot_mslp_anomaly_pdfs(
        hist_large_anom,
        scen_large_anom,
        plot_dir
    )

