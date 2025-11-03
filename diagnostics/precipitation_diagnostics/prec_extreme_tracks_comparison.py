import os
import glob
import json
import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from matplotlib.patches import Patch
import logging
import sys

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# === Configuration ===
threshold = 0.9
delta_time_track = 2 # Number of days before the storm to consider for the large scale
days_prev_prec = 2 # Number of days before the extreme precipitation event to consider for the track
perform_daily_mean = True
# === Seasons ===

seas = "SON"
# === Paths for ERA5 ===

index_path_ERA5 = "/home/ghinassi/work/similarity_pattern_index_pkl/index_pattern_ERA5.pkl"
ERA5_tracks_path = "/home/ghinassi/work/track_output/ERA5/SON/msl/total_tracks/"
ERA5_filtered_path = "/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue/"
ERA5_filtered_file = "concatenated_tracks_lat38_lon4_rad4_lat45_lon8_rad4_1940-2024.txt"
# === Paths for CMIP6 ===

base_index_path = "/home/ghinassi/work/similarity_pattern_index_pkl/"
base_tracks_path = "/home/ghinassi/work/track_output/CMIP6/EC-Earth3/"
vaia_tracks_filename = "concatenated_tracks_lat38_lon4_rad4_lat45_lon8_rad4.txt"

model_name = "EC-Earth3"

def extract_date_bool_dict(filepath, is_excel=True):
    if is_excel:
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath)

    first_col = df.columns[0]
    last_col = df.columns[-1]
    df = df.iloc[:-1]
    df[first_col] = pd.to_datetime(df[first_col])
    df[last_col] = df[last_col].astype(int)
    return dict(zip(df[first_col], df[last_col]))

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


def timestamps_above_threshold(index_path, threshold=0.9, start_year=None, end_year=None, perform_daily_mean=True):
    df = process_index(read_index(index_path), start_year, end_year, daily_mean=perform_daily_mean)
    return [(row.timestamp.strftime('%Y%m%d%H'), row.index_value)
            for row in df.itertuples(index=False) if row.index_value > threshold]


def all_timestamps(index_path, start_year=None, end_year=None, perform_daily_mean=True):
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

def filter_tracks_by_timestamps(tracks, timestamps, delta_time_days=0):
    ts_set = set()
    for ts, _ in timestamps:
        base = datetime.strptime(ts, '%Y%m%d%H')
        ts_set.add(ts)
        if delta_time_days > 0:
            ts_set.add((base + pd.Timedelta(days=delta_time_days)).strftime('%Y%m%d%H'))
    return {k: v for k, v in tracks.items() if any(p[0] in ts_set for p in v["data"])}

def tracks_warning_regions(ERA5_tracks, timestamps_warning_regions):
    timestamps_set = set(timestamps_warning_regions)
    filtered_tracks = {
        track_id: track_info
        for track_id, track_info in ERA5_tracks.items()
        if any(
            datetime.strptime(point[0], "%Y%m%d%H").replace(hour=0, minute=0, second=0, microsecond=0) in timestamps_set
            for point in track_info["data"]
        )
    }
    return filtered_tracks

def compute_probabilities(date_bool_mapping, tracks, index_path, delta_time_track, days_prev_prec, start_year, end_year, season=None):
    # Filter by season if provided
    if season == "SON":
        date_bool_mapping = {
            date: is_extreme
            for date, is_extreme in date_bool_mapping.items()
            if date.month in [9, 10, 11]
        }

    original_extreme_dates = [
        date.replace(hour=0, minute=0, second=0, microsecond=0)
        for date, is_extreme in date_bool_mapping.items() if is_extreme
    ]
    dates_with_extreme = set()
    for date in original_extreme_dates:
        for i in range(days_prev_prec + 1):
            dates_with_extreme.add(date - timedelta(days=i))


    # at first compute the probability of extreme precipitation
    prob_extreme = len(original_extreme_dates) / len(date_bool_mapping) if date_bool_mapping else 0
    
    """
    p(P | S,L) = (# di storm preceduti da large scala che causano pioggia estrema) / 
    (# di storm con large scale)
    
    where P is the extreme precipitation, S is the storm, and L is the large scale pattern
    How is it computed: frst comput the number of tracks with tle large scale pattern (SPI >0.9)
    and then filter the tracks with the extreme precipitation dates.
    """
    # at first find the tracks with the large scale pattern (SPI >0.9)
    
    timestamps_above_large_scale = timestamps_above_threshold(
        index_path, threshold=threshold, start_year=start_year, end_year=end_year
    )
    filtered_tracks_with_large_scale = filter_tracks_by_timestamps(
        tracks, timestamps_above_large_scale, delta_time_track
    )
    
    filtered_tracks_with_large_scale_and_precipitation = tracks_warning_regions(
        filtered_tracks_with_large_scale, dates_with_extreme
    )
    
    # Now compute the probability of extreme precipitation given storm and large scale
    prob_extreme_given_track_and_large_scale = (
        len(filtered_tracks_with_large_scale_and_precipitation) / len(filtered_tracks_with_large_scale)
        if filtered_tracks_with_large_scale else 0
    )
    
    #finally compute P(event) which is P(P|S,L) * P(S|L) * P(L) and should be just len(filtered_tracks_with_large_scale_and_precipitation)/len(timesteps)
    
    """
    P(event) = 
    N_storms_precursor_precip/N_days_total = 
    (N_days_LargeScale/N_days_total) * (N_storms_precursor/N_days_LargeScale)*(N_storms_precursor_precip/N_storms_precursor)
    =
    P(L)*P(S | L)*P(X | S, L) 
    """
    
    all_timestamps_list = all_timestamps(
        index_path, start_year=start_year, end_year=end_year, perform_daily_mean=perform_daily_mean
    )
    
    # POINT TO BE CAREFUL all timestamps are daily mean timestamps so should be equal to N days

    p_event = len(filtered_tracks_with_large_scale_and_precipitation) / len(all_timestamps_list) if all_timestamps_list else 0

    logger.info(f"Total doublepass tracks with extreme precipitation and large scale: {len(filtered_tracks_with_large_scale_and_precipitation)}")
    logger.info(f"Total doublepass tracks with large scale: {len(filtered_tracks_with_large_scale)}")
    logger.info(f"Total doublepass tracks (i.e. simil vaia/florence): {len(tracks)}")
    logger.info(f"Probability of extreme precipitation: {prob_extreme:.4f}")
    logger.info(f"Probability of extreme precipitation given storm and large scale: {prob_extreme_given_track_and_large_scale:.4f}")
    return prob_extreme, prob_extreme_given_track_and_large_scale, p_event


def filter_by_year_range(data_dict, start_year, end_year):
    return {
        k: v for k, v in data_dict.items()
        if start_year <= k.year <= end_year
    }

def filter_tracks_by_year_range(tracks_dict, start_year, end_year):
    def track_in_range(track):
        for point in track["data"]:
            date = datetime.strptime(point[0], "%Y%m%d%H")
            if start_year <= date.year <= end_year:
                return True
        return False

    return {
        tid: tdata for tid, tdata in tracks_dict.items()
        if track_in_range(tdata)
    }

def plot_probabilities(result_data, output_dir, year1_era5, year2_era5, year1_hist, year2_hist, year1_ssp245, year2_ssp245, seas, plot_type="bar"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Extract data
    era5_prob = result_data["era5_prob"]
    era5_prob_given = result_data["era5_prob_given"]
    era5_p_event = result_data["era5_p_event"]

    hist_probs = result_data["hist_probs"]
    ssp_probs = result_data["ssp_probs"]
    hist_probs_given = result_data["hist_probs_given"]
    ssp_probs_given = result_data["ssp_probs_given"]
    hist_p_events = result_data["hist_p_events"]
    ssp_p_events = result_data["ssp_p_events"]

    # Ensemble names
    hist_ens_names = ["Hist " + name for name in result_data.get("hist_ens_names", [f"{i+1}" for i in range(len(hist_probs))])]
    ssp_ens_names = ["ssp245 " + name for name in result_data.get("ssp_ens_names", [f"{i+1}" for i in range(len(ssp_probs))])]

    # Compute ensemble means
    mean_hist_prob = np.mean(hist_probs) if hist_probs else 0
    mean_ssp_prob = np.mean(ssp_probs) if ssp_probs else 0
    mean_hist_prob_given = np.mean(hist_probs_given) if hist_probs_given else 0
    mean_ssp_prob_given = np.mean(ssp_probs_given) if ssp_probs_given else 0
    mean_hist_p_event = np.mean(hist_p_events) if hist_p_events else 0
    mean_ssp_p_event = np.mean(ssp_p_events) if ssp_p_events else 0

    legend_elements = [
        Patch(facecolor="black", label=f"ERA5 ({year1_era5}-{year2_era5})"),
        Patch(facecolor="darkgreen", label=f"Hist ({year1_hist}-{year2_hist})"),
        Patch(facecolor="darkorange", label=f"ssp245 ({year1_ssp245}-{year2_ssp245})"),
    ]

    meanprops = dict(color="black", linestyle="-", linewidth=2.5)

    # ---------- BAR PLOTS ----------
    if plot_type == "bar":
        for values, title, filename, hist_list, ssp_list in [
            (
                [era5_prob] + hist_probs + [mean_hist_prob] + ssp_probs + [mean_ssp_prob],
                f"P(Extreme Precipitation) - {seas}",
                "precipitation_extreme_probability.png",
                hist_probs,
                ssp_probs,
            ),
            (
                [era5_prob_given] + hist_probs_given + [mean_hist_prob_given] + ssp_probs_given + [mean_ssp_prob_given],
                f"P(Extreme Precipitation | Storm, Large Scale) - {seas}",
                "precipitation_given_storm_given_large_scale_probability.png",
                hist_probs_given,
                ssp_probs_given,
            ),
            (
                [era5_p_event] + hist_p_events + [mean_hist_p_event] + ssp_p_events + [mean_ssp_p_event],
                f"P(Event) - {seas}",
                "event_probability.png",
                hist_p_events,
                ssp_p_events,
            ),
        ]:
            plt.figure(figsize=(10, 6))
            x_labels = ["ERA5"] + hist_ens_names + ["Hist ens mean"] + ssp_ens_names + ["ssp245 ens mean"]
            x = list(range(len(x_labels)))
            colors = (
                ["black"]
                + ["limegreen"] * len(hist_list)
                + ["white"]  # placeholder for mean box
                + ["lightsalmon"] * len(ssp_list)
                + ["white"]
            )

            # Bars
            for i, (val, color) in enumerate(zip(values, colors)):
                if (i == 1 + len(hist_ens_names)) or (i == len(x_labels) - 1):
                    continue
                plt.bar(i, val, color=color)

            # Boxplots for ensemble means
            if hist_list:
                plt.boxplot(
                    hist_list,
                    positions=[1 + len(hist_ens_names)],
                    widths=0.6,
                    patch_artist=True,
                    boxprops=dict(facecolor="darkgreen", alpha=0.7),
                    showfliers=False,
                    showmeans=True,
                    meanline=True,
                    meanprops=meanprops,
                    medianprops=dict(color="none"),
                )

            if ssp_list:
                plt.boxplot(
                    ssp_list,
                    positions=[len(x_labels) - 1],
                    widths=0.6,
                    patch_artist=True,
                    boxprops=dict(facecolor="orange", alpha=0.7),
                    showfliers=False,
                    showmeans=True,
                    meanline=True,
                    meanprops=meanprops,
                    medianprops=dict(color="none"),
                )

            plt.xticks(x, x_labels, rotation=45, ha="right")
            plt.ylabel("Probability")
            plt.title(title)
            plt.legend(handles=legend_elements, loc="upper right")
            plt.grid(True, axis="y", linestyle="--", alpha=0.4)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, filename), dpi=300)
            plt.close()
            print(f"Plot saved to {os.path.join(output_dir, filename)}")

    # ---------- BOX PLOTS ----------
    elif plot_type == "box":
        plot_items = [
            (hist_probs, ssp_probs, era5_prob, f"P(Extreme Precipitation) - {seas}", "boxplot_precipitation_extreme_probability.png"),
            (hist_probs_given, ssp_probs_given, era5_prob_given, f"P(Extreme Precipitation | Storm, Large Scale) - {seas}", "boxplot_precipitation_given_storm_given_large_scale_probability.png"),
            (hist_p_events, ssp_p_events, era5_p_event, f"P(Event) - {seas}", "boxplot_event_probability.png"),
        ]

        for hist_list, ssp_list, era5_val, title, filename in plot_items:
            plt.figure(figsize=(8, 6))
            plt.boxplot(
                [hist_list, ssp_list],
                labels=[f"Hist ({year1_hist}-{year2_hist})", f"ssp245 ({year1_ssp245}-{year2_ssp245})"],
                patch_artist=True,
                boxprops=dict(facecolor="lightblue"),
                showfliers=False,
                showmeans=True,
                meanline=True,
                meanprops=meanprops,
                medianprops=dict(color="none"),
            )
            plt.scatter([1], [era5_val], color="red", label=f"ERA5 ({year1_era5}-{year2_era5})", zorder=5)
            plt.ylabel("Probability")
            plt.title(title)
            plt.legend(loc="upper right")
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, filename), dpi=300)
            plt.close()
            print(f"Plot saved to {os.path.join(output_dir, filename)}")

    else:
        raise ValueError("Invalid plot_type. Use 'bar' or 'box'.")


def main():
    save_plot = True
    print_txt = True
    compute_probabilities_bool = True
    # Define paths and parameters
    result_file = "/home/ghinassi/precipitation_diagnostics/json_file_probabilities/precipitation_probabilities_given_storm_and_large_scale.json"
    output_dir = "/home/ghinassi/work/track_plots/precipitation_extremes"
    output_file_txt = os.path.join("/home/ghinassi/work/track_plots/risk_ratio_probabilities/precipitation_extreme_probabilities.txt")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Define years for different datasets
    # ERA5: 1984-2014, Historical: 1984-2014, SSP245: 2070-2100

    year1_era5, year2_era5 = 1984, 2014
    year1_hist, year2_hist = 1984, 2014
    year1_ssp245, year2_ssp245 = 2070, 2100
    

    if not compute_probabilities_bool:
        print("Loading pre-computed probabilities from JSON file...")
        with open(result_file, "r") as f:
            result_data = json.load(f)
    else:
        print("Computing probabilities from scratch...")

        print(f"Processing ERA5 data from {year1_era5} to {year2_era5}, season: {seas}")
        # ERA5 data
        era5_warning_file = "/home/ghinassi/precipitation_diagnostics/ERA5/ERA5_19500101_20241231_P99_direct_noaverage_italy_gridpoint.csv"
        print("era5_warning_file:", era5_warning_file)
        era5_track_path = "/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue/"
        era5_track_file = "concatenated_tracks_lat38_lon4_rad4_lat45_lon8_rad4_1940-2024.txt"
        era5_dates = extract_date_bool_dict(era5_warning_file, is_excel=False)
        era5_dates = filter_by_year_range(era5_dates, year1_era5, year2_era5)
        era5_tracks = read_tracks(era5_track_path, era5_track_file)
        era5_tracks = filter_tracks_by_year_range(era5_tracks, year1_era5, year2_era5)
        print(len(era5_tracks), "tracks found in ERA5 data.")
        index_path_ERA5 = "/home/ghinassi/work/similarity_pattern_index_pkl/index_pattern_ERA5.pkl"
        era5_prob, era5_prob_given, era5_p_event = compute_probabilities(
                era5_dates, era5_tracks, index_path_ERA5,
                delta_time_track, days_prev_prec, year1_era5, year2_era5, season=seas
            )
        print(f"ERA5: P(extreme) = {era5_prob:.4f}, P(extreme | track | large scale) = {era5_prob_given:.4f}, P(event) = {era5_p_event:.4f}")

        model = "EC-Earth3"
        warning_region_path = "/home/ghinassi/work/ENCIRCLE_precipitation/output_precipitation_warning_regions"
        warning_pattern = "EC-Earth3_concatenated_hist+ssp245_*_19500101_20991231_P99_direct_noaverage_italy_gridpoint.xlsx"
        track_filename = "concatenated_tracks_lat38_lon4_rad4_lat45_lon8_rad4.txt"

        hist_probs, ssp_probs = [], []
        hist_probs_given, ssp_probs_given = [], []
        hist_p_events, ssp_p_events = [], []
        hist_ens_names, ssp_ens_names = [], []

        files = glob.glob(os.path.join(warning_region_path, warning_pattern))
        print(f"\nProcessing {model} model, season: {seas}")
        print(f"years for historical: {year1_hist}-{year2_hist}, ssp245: {year1_ssp245}-{year2_ssp245}")
        print(f"Found {len(files)} warning regions files.")

        for warning_file in files:
            print(f"\nProcessing file: {warning_file}")
            ensemble = warning_file.split("_")[7]
            print(f"\nProcessing ensemble: {ensemble}")

            hist_track_dir = f"/home/ghinassi/work/track_output/CMIP6/{model}/historical/{seas}/{ensemble}/psl/vaia_analogue"
            ssp_track_dir = f"/home/ghinassi/work/track_output/CMIP6/{model}/scenarioMIP/ssp245/{seas}/{ensemble}/psl/vaia_analogue"

            if os.path.isfile(os.path.join(hist_track_dir, track_filename)):
                index_file = os.path.join(base_index_path, f"index_pattern_{model}_historical_{ensemble}.pkl")
                logger.info(f"Using Similarity Pattern Index index file: {index_file}")
                hist_dates = extract_date_bool_dict(warning_file, is_excel=True)
                hist_dates = filter_by_year_range(hist_dates, year1_hist, year2_hist)
                hist_tracks = read_tracks(hist_track_dir, track_filename)
                hist_tracks = filter_tracks_by_year_range(hist_tracks, year1_hist, year2_hist)
                p, pg, pe = compute_probabilities(hist_dates, hist_tracks, 
                    index_file, delta_time_track, days_prev_prec, year1_hist, year2_hist, season=seas)
                hist_probs.append(p)
                hist_probs_given.append(pg)
                hist_p_events.append(pe)
                hist_ens_names.append(ensemble) 

            if os.path.isfile(os.path.join(ssp_track_dir, track_filename)):
                index_file = os.path.join(base_index_path, f"index_pattern_{model}_scenarioMIP_ssp245_{ensemble}.pkl")
                ssp_dates = extract_date_bool_dict(warning_file, is_excel=True)
                ssp_dates = filter_by_year_range(ssp_dates, year1_ssp245, year2_ssp245)
                ssp_tracks = read_tracks(ssp_track_dir, track_filename)
                ssp_tracks = filter_tracks_by_year_range(ssp_tracks, year1_ssp245, year2_ssp245)
                p, pg, pe = compute_probabilities(ssp_dates, ssp_tracks, 
                    index_file, delta_time_track, days_prev_prec, year1_ssp245, year2_ssp245, season=seas)
                ssp_probs.append(p)
                ssp_probs_given.append(pg)
                ssp_p_events.append(pe)
                ssp_ens_names.append(ensemble)

        result_data = {
            "era5_prob": era5_prob,
            "era5_prob_given": era5_prob_given,
            "era5_p_event": era5_p_event,
            "hist_probs": hist_probs,
            "hist_probs_given": hist_probs_given,
            "hist_p_events": hist_p_events,
            "hist_ens_names": hist_ens_names,
            "ssp_probs": ssp_probs,
            "ssp_probs_given": ssp_probs_given,
            "ssp_p_events": ssp_p_events,
            "ssp_ens_names": ssp_ens_names
        }

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        print(f"\nSaving results to {result_file}...")
        with open(result_file, "w") as f:
            json.dump(result_data, f, indent=2)

    if save_plot:
        plot_probabilities(result_data, output_dir, year1_era5, year2_era5,
                   year1_hist, year2_hist, year1_ssp245, year2_ssp245,
                   seas, plot_type="bar")

    if print_txt:
        with open(output_file_txt, "w") as f:
            f.write("\nPrecipitation probabilities:\n")
            f.write(f"ERA5: P(extreme) = {result_data['era5_prob']:.4f}, "
                    f"P(extreme | storm, large scale) = {result_data['era5_prob_given']:.4f}, "
                    f"P(event) = {result_data['era5_p_event']:.4f}\n")
            f.write("Historical:\n")
            for name, prob in zip(result_data["hist_ens_names"], result_data["hist_probs"]):
                f.write(f"HIST {name}: P(extreme) = {prob:.4f}, "
                        f"P(extreme | storm, large scale) = {result_data['hist_probs_given'][result_data['hist_ens_names'].index(name)]:.4f}, "
                        f"P(event) = {result_data['hist_p_events'][result_data['hist_ens_names'].index(name)]:.4f}\n")
            if result_data["hist_probs"]:
                mean_hist_prob = np.mean(result_data["hist_probs"])
                mean_hist_prob_given = np.mean(result_data["hist_probs_given"])
                mean_hist_p_event = np.mean(result_data["hist_p_events"])
                f.write(f"Hist ens mean: P(extreme) = {mean_hist_prob:.4f}, "
                        f"P(extreme | storm, large scale) = {mean_hist_prob_given:.4f}, "
                        f"P(event) = {mean_hist_p_event:.4f}\n")
            f.write("SSP245:\n")
            for name, prob in zip(result_data["ssp_ens_names"], result_data["ssp_probs"]):
                f.write(f"SSP245 {name}: P(extreme) = {prob:.4f}, "
                        f"P(extreme | storm, large scale) = {result_data['ssp_probs_given'][result_data['ssp_ens_names'].index(name)]:.4f}, "
                        f"P(event) = {result_data['ssp_p_events'][result_data['ssp_ens_names'].index(name)]:.4f}\n")
            if result_data["ssp_probs"]:
                mean_ssp_prob = np.mean(result_data["ssp_probs"])
                mean_ssp_prob_given = np.mean(result_data["ssp_probs_given"])
                mean_ssp_p_event = np.mean(result_data["ssp_p_events"])
                f.write(f"SSP245 ens mean: P(extreme) = {mean_ssp_prob:.4f}, "
                        f"P(extreme | storm, large scale) = {mean_ssp_prob_given:.4f}, "
                        f"P(event) = {mean_ssp_p_event:.4f}\n")
            # file saved to output_dir
            sys.__stdout__.write(f"file saved to {output_file_txt}\n")
        
if __name__ == "__main__":
    main()

