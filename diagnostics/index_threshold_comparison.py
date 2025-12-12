import os
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sys
from matplotlib.patches import Patch
import scipy.stats as st
import re

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

# Independent year ranges for datasets
start_year_ERA5 = 1984
end_year_ERA5 = 2014

start_year_hist = 1984
end_year_hist = 2014

start_year_scen = 2070
end_year_scen = 2100

# Redirect all print output to a text file
outputh_path = "/home/ghinassi/work/track_plots/summary_index_probability/"
verbose_output_file = "index_threshold_comparison_verbose.txt"
output_file = "index_threshold_comparison_output.txt"

print_verbose = True  # Set to False to disable verbose output
if not os.path.exists(outputh_path):
    os.makedirs(outputh_path, exist_ok=True)
if print_verbose:
    sys.stdout = Logger(os.path.join(outputh_path, verbose_output_file))
    sys.__stdout__.write(f"Verbose output will be saved to: {os.path.join(outputh_path, verbose_output_file)}\n")

print_txt = True  # Set to False to disable summary output


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

def read_tracks_for_weights(filepath):
    """
    Read track counts from a summary file to compute weights for flattened ensemble means.
    Expected lines:
    ERA5 (1984-2014): total_ts=2821, largescale_timesteps=100, total_tracks=36, large_scale=11, large+precip=3
    Historical r2i1p1f1: total_ts=2821, largescale_timesteps=135, total_tracks=49, large_scale=14, large+precip=3
    ...
    ssp245 r25i1p1f1: total_ts=2821, largescale_timesteps=12, total_tracks=41, large_scale=5, large+precip=3
    ...
    """
    hist_counts = {}
    ssp_counts = {}
    with open(filepath, "r") as f:
        for line in f:
            hist_match = re.match(r"Historical\s+(r\d+i1p1f1):\s*total_ts=(\d+),\s*largescale_timesteps=(\d+),\s*total_tracks=(\d+),\s*large_scale=(\d+),\s*large\+precip=(\d+)", line)
            ssp_match = re.match(r"ssp245\s+(r\d+i1p1f1):\s*total_ts=(\d+),\s*largescale_timesteps=(\d+),\s*total_tracks=(\d+),\s*large_scale=(\d+),\s*large\+precip=(\d+)", line)
            if hist_match:
                member = hist_match.group(1)
                total_ts = int(hist_match.group(2))
                large_scale_ts = int(hist_match.group(3))
                total_tracks = int(hist_match.group(4))
                large_scale = int(hist_match.group(5))
                large_precip = int(hist_match.group(6))
                hist_counts[member] = {
                    "total_ts": total_ts,
                    "largescale_timesteps": large_scale_ts,
                    "total_tracks": total_tracks,
                    "large_scale": large_scale,
                    "large_precip": large_precip
                }
            elif ssp_match:
                member = ssp_match.group(1)
                total_ts = int(ssp_match.group(2))
                large_scale_ts = int(ssp_match.group(3))
                total_tracks = int(ssp_match.group(4))
                large_scale = int(ssp_match.group(5))
                large_precip = int(ssp_match.group(6))
                ssp_counts[member] = {
                    "total_ts": total_ts,
                    "largescale_timesteps": large_scale_ts,
                    "total_tracks": total_tracks,
                    "large_scale": large_scale,
                    "large_precip": large_precip
                }
    return hist_counts, ssp_counts

def weighted_mean(values, weights):
    values, weights = np.array(values), np.array(weights)
    if np.sum(weights) == 0:
        return np.mean(values)
    return np.sum(values * weights) / np.sum(weights)

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
print("a daily mean is performed on the SPIndex" if perform_daily_mean else "no daily mean is performed on the idnex")
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


# === EC-Earth3 Analysis ===

def analyze_ec_earth(expn, expt, ens_list, start_year, end_year):
    label = f"{expn}_{expt}" if expn == "scenarioMIP" else expn
    label_path = f"{expn}/{expt}" if expn == "scenarioMIP" else expn
    vaia_tracks_filename = vaia_tracks_filename_scen if expn == "scenarioMIP" else vaia_tracks_filename_hist
    probs_pattern = []
    probs_storm = []
    print(f"\n=== {model_name} ===")
    for ens in ens_list:
        index_file = os.path.join(base_index_path, f"index_pattern_{model_name}_{label}_{ens}.pkl")
        timestamps = timestamps_above_threshold(index_file, threshold, start_year, end_year)
        all_ts = all_timestamps(index_file, start_year, end_year)
        print(f"\nProcessing {label} {ens}...")
        print(f"Threshold: {threshold}")
        print(f"Start year: {start_year}, End year: {end_year}")
        print(f"first date is {all_ts[0][0]} and last date is {all_ts[-1][0]}")
        track_dir = os.path.join(base_tracks_path, label_path, "SON", ens, "psl/total_tracks/")
        vaia_dir = os.path.join(base_tracks_path, label_path, "SON", ens, "psl/vaia_analogue")

        total_tracks = read_tracks(track_dir, f"concatenated_tracks_{ens}.txt")
        vaia_tracks = read_tracks(vaia_dir, vaia_tracks_filename)

        #filtered = filter_tracks_by_timestamps(total_tracks, timestamps, delta_time)
        filtered_vaia = filter_tracks_by_timestamps(vaia_tracks, timestamps, delta_time)

        p_pattern = len(timestamps) / len(all_ts) if all_ts else 0
        p_storm = len(filtered_vaia) / len(timestamps) if timestamps else 0

        probs_pattern.append(p_pattern)
        probs_storm.append(p_storm)
        
        print(f"Total number of timestamps: {len(all_ts)}")
        if perform_daily_mean:
            print(f"Number of days above threshold: {len(timestamps)}")
        else:
            print(f"Number of timestamps above threshold: {len(timestamps)}")
        print(f"Number of filtered VAIAlike tracks: {len(filtered_vaia)}")
        print(f"P(pattern): {p_pattern:.3f}")
        print(f"P(storm | pattern): {p_storm:.3f}")

    return probs_pattern, probs_storm

pattern_hist, storm_hist = analyze_ec_earth("historical", "", ens_list_hist, start_year_hist, end_year_hist)
pattern_scen, storm_scen = analyze_ec_earth("scenarioMIP", "ssp245", ens_list_scen, start_year_scen, end_year_scen)

#print mean probabilities
mean_pattern_hist = np.mean(pattern_hist)
mean_storm_hist = np.mean(storm_hist)
mean_pattern_scen = np.mean(pattern_scen)
mean_storm_scen = np.mean(storm_scen)
print(f"\n=== EC-Earth3 historical ens mean ===")
print(f"start year: {start_year_hist}, end year: {end_year_hist}")
print(f"P(pattern): {mean_pattern_hist:.3f}")
print(f"P(storm | pattern): {mean_storm_hist:.3f}")
print(f"\n=== EC-Earth3 scenarioMIP ssp245 ens mean ===")
print(f"start year: {start_year_scen}, end year: {end_year_scen}")
print(f"P(pattern): {mean_pattern_scen:.3f}")
print(f"P(storm | pattern): {mean_storm_scen:.3f}")

# === PLOT ===

# Helper function: mean and 95% CI
def mean_ci(data, confidence=0.95):
    if len(data) < 2:
        return np.mean(data), 0
    mean = np.mean(data)
    sem = np.std(data, ddof=1) / np.sqrt(len(data))
    ci = sem * st.t.ppf((1 + confidence) / 2., len(data) - 1)
    return mean, ci

def plot_storm_given_pattern(
        prob_ERA5, prob_hist, prob_scen,
        labels_hist, labels_scen, plot_dir,
        hist_counts, ssp_counts,
        plot_type="bar"):

    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    # ------------------------------------------------------
    # --- Construct weights (largescale_timesteps)
    # ------------------------------------------------------
    hist_weights = [
        hist_counts[ens.replace("HIST ", "")]["largescale_timesteps"]
        for ens in labels_hist
    ]

    scen_weights = [
        ssp_counts[ens.replace("SSP245 ", "")]["largescale_timesteps"]
        for ens in labels_scen
    ]

    # Weighted ensemble means (for plotting only)
    w_mean_hist = weighted_mean(prob_hist, hist_weights)
    w_mean_scen = weighted_mean(prob_scen, scen_weights)


    # ------------------------------------------------------
    # --- PLOT
    # ------------------------------------------------------
    if plot_type == "bar":

        x_labels = ["ERA5"] + labels_hist + ["Hist ens mean"] \
                   + labels_scen + ["ssp245 ens mean"]
        values = [prob_ERA5] + prob_hist + [np.nan] \
                 + prob_scen + [np.nan]
        x = list(range(len(x_labels)))

        colors = (
            ["black"] +
            ["limegreen"] * len(prob_hist) +
            ["white"] +
            ["lightsalmon"] * len(prob_scen) +
            ["white"]
        )

        plt.figure(figsize=(12, 6))

        # Bars: unchanged
        for i, val in enumerate(values):
            if not np.isnan(val):
                plt.bar(x[i], val, color=colors[i])

        # --------------------------------------------------
        # Weighted ensemble means as dots with CI
        # --------------------------------------------------
        pos_hist = len(["ERA5"] + labels_hist)
        pos_scen = len(["ERA5"] + labels_hist + ["Hist ens mean"] + labels_scen)

        # Hist weighted mean and CI
        if prob_hist:
            mean_hist, ci_hist = mean_ci(prob_hist)
            plt.errorbar(
                pos_hist, w_mean_hist, yerr=ci_hist,
                fmt='o', color='darkgreen', ecolor='black',
                capsize=5
            )
        # SSP245 weighted mean and CI
        if prob_scen:
            mean_scen, ci_scen = mean_ci(prob_scen)
            plt.errorbar(
                pos_scen, w_mean_scen, yerr=ci_scen,
                fmt='o', color='darkorange', ecolor='black',
                capsize=5
            )

        legend_elements = [
            Patch(facecolor="black", label="ERA5 (1984-2014)"),
            Patch(facecolor="darkgreen", label="Hist members"),
            Patch(facecolor="orange", label="SSP245 members"),
        ]

        plt.xticks(x, x_labels, rotation=45, ha="right")
        plt.ylabel("Probability")
        plt.title("P(Storm | Large scale)")
        plt.legend(handles=legend_elements, loc="upper right")
        plt.grid(True, axis='y', linestyle='--', alpha=0.4)
        plt.tight_layout()

        plot_path = os.path.join(plot_dir, "storm_given_pattern_hist_summary.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()

        print(f"Plot saved to: {plot_path}")


    elif plot_type == "box":
        plt.figure(figsize=(8, 6))
        plt.boxplot(
            [prob_hist, prob_scen],
            labels=["Hist", "ssp245"],
            patch_artist=True,
            boxprops=dict(facecolor="lightblue"),
            showfliers=False,
            showmeans=True,
            meanline=True,
            meanprops=dict(color="black", linewidth=2.5),
            medianprops=dict(color="none")
        )
        plt.scatter([1], [prob_ERA5], color="red", label="ERA5", zorder=5)
        plt.ylabel("Probability")
        plt.title("P(Storm | Large scale)")
        plt.legend(loc="upper right")
        plt.tight_layout()

        plot_path = os.path.join(plot_dir, "boxplot_storm_given_pattern.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()
        print(f"Plot saved to: {plot_path}")

    else:
        raise ValueError("Invalid plot_type. Use 'bar' or 'box'.")

def plot_pattern_probability(prob_ERA5, prob_hist, prob_scen, labels_hist, labels_scen, plot_dir, plot_type="bar"):
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)

    mean_hist = np.mean(prob_hist) if prob_hist else 0
    mean_scen = np.mean(prob_scen) if prob_scen else 0

    # Common mean line style (thick, solid black)
    meanprops = dict(color="black", linestyle="-", linewidth=2.5)

    if plot_type == "bar":
        x_labels = ["ERA5"] + labels_hist + ["Hist ens mean"] + labels_scen + ["ssp245 ens mean"]
        values = [prob_ERA5] + prob_hist + [np.nan] + prob_scen + [np.nan]
        x = list(range(len(x_labels)))

        colors = (
            ["black"] +
            ["limegreen"] * len(prob_hist) +
            ["white"] +  # placeholder for box
            ["lightsalmon"] * len(prob_scen) +
            ["white"]    # placeholder for box
        )

        legend_elements = [
            Patch(facecolor="black", label="ERA5 (1984-2014)"),
            Patch(facecolor="darkgreen", label="Hist (1984-2014)"),
            Patch(facecolor="orange", label="ssp245 (2070-2100)"),
        ]

        plt.figure(figsize=(12, 6))
        # Bar plot for individual ensemble members
        for i, val in enumerate(values):
            if not np.isnan(val):
                plt.bar(x[i], val, color=colors[i])
        # Plot ensemble means as dots + 95% CI error bars
        if prob_hist:
            mean_hist, ci_hist = mean_ci(prob_hist)
            pos_hist = len(["ERA5"] + labels_hist)
            plt.errorbar(
                pos_hist, mean_hist, yerr=ci_hist,
                fmt='o', color='darkgreen', ecolor='black',
                capsize=5
            )
        if prob_scen:
            mean_scen, ci_scen = mean_ci(prob_scen)
            pos_scen = len(["ERA5"] + labels_hist + ["Hist ens mean"] + labels_scen)
            plt.errorbar(
                pos_scen, mean_scen, yerr=ci_scen,
                fmt='o', color='darkorange', ecolor='black',
                capsize=5
            )
            
        
        plt.xticks(x, x_labels, rotation=45, ha="right")
        plt.ylabel("Probability")
        plt.title("P(Large scale)")
        plt.legend(handles=legend_elements, loc="upper right")
        plt.grid(True, axis='y', linestyle='--', alpha=0.4)
        plt.tight_layout()

        plot_path = os.path.join(plot_dir, "large_scale_pattern_probability_hist_summary.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()
        print(f"Plot saved to: {plot_path}")

    elif plot_type == "box":
        plt.figure(figsize=(8, 6))
        plt.boxplot(
            [prob_hist, prob_scen],
            labels=["Hist", "ssp245"],
            patch_artist=True,
            boxprops=dict(facecolor="lightblue"),
            showfliers=False,
            showmeans=True,
            meanline=True,
            meanprops=meanprops,
            medianprops=dict(color="none")
        )
        plt.scatter([1], [prob_ERA5], color="red", label="ERA5", zorder=5)
        plt.ylabel("Probability")
        plt.title("P(Large scale)")
        plt.legend(loc="upper right")
        plt.tight_layout()

        plot_path = os.path.join(plot_dir, "boxplot_large_scale_pattern_probability.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()

    else:
        raise ValueError("Invalid plot_type. Use 'bar' or 'box'.")


    
# finally plot the results
labels_hist = [f"HIST {ens}" for ens in ens_list_hist]
labels_scen = [f"SSP245 {ens}" for ens in ens_list_scen]

# read weights for ensemble members
hist_counts, ssp_counts = read_tracks_for_weights("/home/ghinassi/work/track_plots/risk_ratio_probabilities/track_counts_summary.txt")

plot_storm_given_pattern(
    prob_storm_given_pattern_ERA5,
    storm_hist, storm_scen,
    labels_hist, labels_scen,
    plot_dir,
    hist_counts, ssp_counts,   # <-- add these
    plot_type="bar"
)

plot_pattern_probability(prob_pattern_ERA5, pattern_hist, pattern_scen, labels_hist, labels_scen, plot_dir, plot_type="bar")

#now plot box plots
#plot_storm_given_pattern(prob_storm_given_pattern_ERA5, storm_hist, storm_scen, labels_hist, labels_scen, plot_dir, plot_type="box")
#plot_pattern_probability(prob_pattern_ERA5, pattern_hist, pattern_scen, labels_hist, labels_scen, plot_dir, plot_type="box")

# Print summary to text file
if print_txt:
    output_txt_path = os.path.join(outputh_path, output_file)
    with open(output_txt_path, "w") as out:
        out.write("Large-scale Pattern and Storm Probabilities\n")
        out.write("ERA5: P(pattern) = {:.4f}, P(storm | pattern) = {:.4f}\n".format(
            prob_pattern_ERA5, prob_storm_given_pattern_ERA5))
        out.write("Historical:\n")
        for ens, p_pattern, p_storm in zip(labels_hist, pattern_hist, storm_hist):
            out.write(f"{ens}: P(pattern) = {p_pattern:.4f}, P(storm | pattern) = {p_storm:.4f}\n")
        out.write(f"Hist ens mean: P(pattern) = {mean_pattern_hist:.4f}, P(storm | pattern) = {mean_storm_hist:.4f}\n")
        out.write("ScenarioMIP ssp245:\n")
        for ens, p_pattern, p_storm in zip(labels_scen, pattern_scen, storm_scen):
            out.write(f"{ens}: P(pattern) = {p_pattern:.4f}, P(storm | pattern) = {p_storm:.4f}\n")
        out.write(f"SSP245 ens mean: P(pattern) = {mean_pattern_scen:.4f}, P(storm | pattern) = {mean_storm_scen:.4f}\n")

    sys.__stdout__.write(f"Summary written to: {output_txt_path}\n")
    
