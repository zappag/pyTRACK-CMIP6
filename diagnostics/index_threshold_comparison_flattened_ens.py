import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sys
from matplotlib.patches import Patch

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
delta_time = 48
perform_daily_mean = True

# Independent year ranges for datasets
start_year_ERA5 = 1984
end_year_ERA5 = 2014

start_year_hist = 1984
end_year_hist = 2014

start_year_scen = 2070
end_year_scen = 2100

# Redirect all print output to a text file
outputh_path = "/home/ghinassi/work/track_plots/summary_index_probability/"
#verbose_output_file = "index_threshold_comparison_verbose.txt"
output_file = "index_threshold_comparison_output_flattened_ens.txt"

print_verbose = False  # Set to False to disable verbose output
if not os.path.exists(outputh_path):
    os.makedirs(outputh_path, exist_ok=True)
if print_verbose:
    sys.stdout = Logger(os.path.join(outputh_path, verbose_output_file))
    sys.__stdout__.write(f"Verbose output will be saved to: {os.path.join(outputh_path, verbose_output_file)}\n")

print_txt = True  # Set to False to disable summary output

# === Paths ===
index_path_ERA5 = "/home/ghinassi/work/similarity_pattern_index_pkl/index_pattern_ERA5.pkl"
ERA5_tracks_path = "/home/ghinassi/work/track_output/ERA5/SON/msl/total_tracks/"
ERA5_filtered_path = "/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue/"
ERA5_filtered_file = "concatenated_tracks_lat38_lon4_rad4_lat45_lon8_rad4_1940-2024.txt"

base_index_path = "/home/ghinassi/work/similarity_pattern_index_pkl/"
base_tracks_path = "/home/ghinassi/work/track_output/CMIP6/EC-Earth3/"
vaia_tracks_filename = "concatenated_tracks_lat38_lon4_rad4_lat45_lon8_rad4.txt"

model_name = "EC-Earth3"

#directory for plotting
plot_dir = "/home/ghinassi/work/track_plots/storm_given_pattern/"
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

# === Utility Functions ===

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

prob_pattern_ERA5 = len(timestamps_ERA5) / len(all_ts_ERA5)
prob_storm_given_pattern_ERA5 = len(filtered_vaia_ERA5) / len(timestamps_ERA5)

print("\n=== ERA5 ===")
print("a daily mean is performed on the SPIndex" if perform_daily_mean else "no daily mean is performed on the index")
print(f"Threshold: {threshold}")
print(f"Start year: {start_year_ERA5}, End year: {end_year_ERA5}")
print(f"first date is {all_ts_ERA5[0][0]} and last date is {all_ts_ERA5[-1][0]}")
print(f"Total number of timestamps: {len(all_ts_ERA5)}")
if perform_daily_mean:
    print(f"Number of days above threshold: {len(timestamps_ERA5)}")
else:
    print(f"Number of timestamps above threshold: {len(timestamps_ERA5)}")
print(f"Number of filtered VAIAlike tracks: {len(filtered_vaia_ERA5)}")
print(f"P(pattern): {prob_pattern_ERA5:.3f}")
print(f"P(storm | pattern): {prob_storm_given_pattern_ERA5:.3f}")


# === EC-Earth3 Flattened Ensemble Analysis ===

def analyze_ec_earth_flat(expn, expt, ens_list, start_year, end_year):
    """Compute P(pattern) and P(storm|pattern) for the flattened ensemble (merged members)."""
    label = f"{expn}_{expt}" if expn == "scenarioMIP" else expn
    label_path = f"{expn}/{expt}" if expn == "scenarioMIP" else expn

    all_timestamps_flat = []
    timestamps_above_flat = []
    filtered_vaia_flat = []

    for ens in ens_list:
        index_file = os.path.join(base_index_path, f"index_pattern_{model_name}_{label}_{ens}.pkl")
        ts_above = timestamps_above_threshold(index_file, threshold, start_year, end_year)
        ts_all = all_timestamps(index_file, start_year, end_year)
        all_timestamps_flat.extend(ts_all)
        timestamps_above_flat.extend(ts_above)

        # read storm tracks
        vaia_dir = os.path.join(base_tracks_path, label_path, "SON", ens, "psl/vaia_analogue")
        vaia_tracks = read_tracks(vaia_dir, vaia_tracks_filename)

        filtered_vaia = filter_tracks_by_timestamps(vaia_tracks, ts_above, delta_time)
        filtered_vaia_flat.extend(filtered_vaia.values())

    # compute flattened probabilities
    p_pattern = len(timestamps_above_flat) / len(all_timestamps_flat) if all_timestamps_flat else 0
    p_storm = len(filtered_vaia_flat) / len(timestamps_above_flat) if timestamps_above_flat else 0

    print(f"\n=== {model_name} {label} (flattened ensemble) ===")
    print(f"Start year: {start_year}, End year: {end_year}")
    print(f"Total timestamps: {len(all_timestamps_flat)}")
    print(f"Timestamps above threshold: {len(timestamps_above_flat)}")
    print(f"Filtered VAIAlike tracks: {len(filtered_vaia_flat)}")
    print(f"P(pattern): {p_pattern:.3f}")
    print(f"P(storm | pattern): {p_storm:.3f}")

    return p_pattern, p_storm


# Flattened historical and scenario results
prob_pattern_hist, prob_storm_hist = analyze_ec_earth_flat("historical", "", ens_list_hist, start_year_hist, end_year_hist)
prob_pattern_scen, prob_storm_scen = analyze_ec_earth_flat("scenarioMIP", "ssp245", ens_list_scen, start_year_scen, end_year_scen)


# === Simplified PLOT ===

def plot_three_bars(prob_pattern_ERA5, prob_pattern_hist, prob_pattern_scen,
                    prob_storm_ERA5, prob_storm_hist, prob_storm_scen, plot_dir):
    """Plot only ERA5, flattened historical, and flattened ssp245."""

    labels = ["ERA5", "Historical", "SSP245"]

    # ---- P(Large scale)
    plt.figure(figsize=(6, 5))
    plt.bar(labels, [prob_pattern_ERA5, prob_pattern_hist, prob_pattern_scen],
            color=["black", "darkgreen", "orange"], alpha=0.8)
    plt.ylabel("Probability")
    plt.title("P(Large scale)")
    plt.grid(True, axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    path_large = os.path.join(plot_dir, "large_scale_pattern_probability_flattened_ens.png")
    plt.savefig(path_large, dpi=300)
    plt.close()
    print(f"Plot saved to: {path_large}")

    # ---- P(Storm | Large scale)
    plt.figure(figsize=(6, 5))
    plt.bar(labels, [prob_storm_ERA5, prob_storm_hist, prob_storm_scen],
            color=["black", "darkgreen", "orange"], alpha=0.8)
    plt.ylabel("Probability")
    plt.title("P(Storm | Large scale)")
    plt.grid(True, axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    path_storm = os.path.join(plot_dir, "storm_given_pattern_flattened_ens.png")
    plt.savefig(path_storm, dpi=300)
    plt.close()
    print(f"Plot saved to: {path_storm}")


# Plot simplified results
plot_three_bars(
    prob_pattern_ERA5, prob_pattern_hist, prob_pattern_scen,
    prob_storm_given_pattern_ERA5, prob_storm_hist, prob_storm_scen,
    plot_dir
)


# === Simplified text output ===

if print_txt:
    output_txt_path = os.path.join(outputh_path, output_file)
    with open(output_txt_path, "w") as out:
        out.write("=== Large-scale Pattern and Storm Probabilities ===\n\n")
        out.write(f"ERA5: P(pattern) = {prob_pattern_ERA5:.4f}, P(storm | pattern) = {prob_storm_given_pattern_ERA5:.4f}\n")
        out.write(f"Historical (flattened): P(pattern) = {prob_pattern_hist:.4f}, P(storm | pattern) = {prob_storm_hist:.4f}\n")
        out.write(f"SSP245 (flattened): P(pattern) = {prob_pattern_scen:.4f}, P(storm | pattern) = {prob_storm_scen:.4f}\n")

    sys.__stdout__.write(f"Summary written to: {output_txt_path}\n")
