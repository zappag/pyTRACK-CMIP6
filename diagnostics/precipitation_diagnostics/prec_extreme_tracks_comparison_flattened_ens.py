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

logging.basicConfig(level=logging.INFO)
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
ERA5_filtered_file = "concatenated_tracks_firstlatpass39_firstlonpass4_firstrad3.5_secondlatpass45_secondlonpass10_secondrad3.5_box_1940-2024.txt"

# === Paths for CMIP6 ===
model_name = "EC-Earth3"
base_index_path = "/home/ghinassi/work/similarity_pattern_index_pkl/"
base_tracks_path = f"/home/ghinassi/work/track_output/CMIP6/{model_name}/"


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
    """Read a pickle index file and return the dict."""
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

def build_extended_dates(date_bool_mapping, days_prev_prec):
    """
    Given a dict mapping datetimes -> boolean (is_extreme),
    return a set of dates (with hour=0) that includes each extreme date
    and the previous `days_prev_prec` days for each extreme.
    """
    original_extreme_dates = [
        d.replace(hour=0, minute=0, second=0, microsecond=0)
        for d, flag in date_bool_mapping.items() if flag
    ]
    extended_dates = set()
    for dt in original_extreme_dates:
        for i in range(days_prev_prec + 1):
            extended_dates.add(dt - timedelta(days=i))
    return extended_dates



def timestamps_above_threshold(index_data_or_path, threshold=0.9, start_year=None, end_year=None, perform_daily_mean=True):
    """
    Accept either a path to the pickle or a pre-loaded dict.
    Returns list of (YYYYmmddHH, index_value) for timestamps with index_value > threshold.
    """
    if isinstance(index_data_or_path, (str, bytes, os.PathLike)):
        index_data = read_index(index_data_or_path)
    elif isinstance(index_data_or_path, dict):
        index_data = index_data_or_path
    else:
        raise TypeError(f"Invalid type for index_data_or_path: {type(index_data_or_path)}")

    df = process_index(index_data, start_year, end_year, daily_mean=perform_daily_mean)
    return [(row.timestamp.strftime('%Y%m%d%H'), row.index_value)
            for row in df.itertuples(index=False) if row.index_value > threshold]


def all_timestamps(index_data_or_path, start_year=None, end_year=None, perform_daily_mean=True):
    """
    Accept either a path to the pickle or a pre-loaded dict.
    Returns list of (YYYYmmddHH, index_value) for all timestamps (non-NaN)
    """
    if isinstance(index_data_or_path, (str, bytes, os.PathLike)):
        index_data = read_index(index_data_or_path)
    elif isinstance(index_data_or_path, dict):
        index_data = index_data_or_path
    else:
        raise TypeError(f"Invalid type for index_data_or_path: {type(index_data_or_path)}")

    df = process_index(index_data, start_year, end_year, daily_mean=perform_daily_mean)
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

def compute_probabilities_ERA5(date_bool_mapping, tracks, index_data_or_path,
                
                          delta_time_track, days_prev_prec, start_year, end_year,
                          season=None, ensemble_count=1):
    
    # If index_data_or_path is a path, load it; if it is dict, use directly.
    if isinstance(index_data_or_path, (str, bytes, os.PathLike)):
        index_data = read_index(index_data_or_path)
    elif isinstance(index_data_or_path, dict):
        index_data = index_data_or_path
    else:
        raise TypeError(f"Invalid type for index_data_or_path: {type(index_data_or_path)}")

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

    # timestamps_above_threshold and all_timestamps now accept dicts or paths
    timestamps_above_large_scale = timestamps_above_threshold(
        index_data, threshold=threshold, start_year=start_year, end_year=end_year, perform_daily_mean=perform_daily_mean
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

    all_timestamps_list = all_timestamps(
        index_data, start_year=start_year, end_year=end_year, perform_daily_mean=perform_daily_mean
    )

    # --- FIX: account for ensemble members by multiplying total time steps by ensemble_count ---
    total_time_steps = len(all_timestamps_list) * max(1, int(ensemble_count))
    p_event = len(filtered_tracks_with_large_scale_and_precipitation) / total_time_steps if total_time_steps else 0

    logger.info(f"Total doublepass tracks with extreme precipitation and large scale: {len(filtered_tracks_with_large_scale_and_precipitation)}")
    logger.info(f"Total doublepass tracks with large scale: {len(filtered_tracks_with_large_scale)}")
    logger.info(f"Total doublepass tracks (i.e. simil vaia/florence): {len(tracks)}")
    logger.info(f"Probability of extreme precipitation: {prob_extreme:.4f}")
    logger.info(f"Probability of extreme precipitation given storm and large scale: {prob_extreme_given_track_and_large_scale:.4f}")
    logger.info(f"length all timestamps (single-member): {len(all_timestamps_list)}")
    logger.info(f"ensemble members count: {ensemble_count}")
    logger.info(f"total_time_steps (length * ensemble_count): {total_time_steps}")
    logger.info(f"Probability of event: {p_event:.6f}")
    return prob_extreme, prob_extreme_given_track_and_large_scale, p_event


def compute_probabilities_flattened(date_bool_mapping, tracks, index_data_or_path,
                          tracks_all=None, tracks_with_large_scale=None, tracks_with_large_scale_and_precipitation=None,
                          delta_time_track=0, days_prev_prec=0, start_year=None, end_year=None,
                          season=None, ensemble_count=1):
    """
    Compute the same set of probabilities as compute_probabilities_ERA5, but for flattened/concatenated ensembles.
    This function computes track counts from the provided `tracks` and `index_data_or_path` to avoid mismatches.
    Optional numeric totals (tracks_all, tracks_with_large_scale, tracks_with_large_scale_and_precipitation)
    are accepted for diagnostics only — the function will recompute counts and log a warning if they disagree.
    """

    # Load index
    if isinstance(index_data_or_path, (str, bytes, os.PathLike)):
        index_data = read_index(index_data_or_path)
    elif isinstance(index_data_or_path, dict):
        index_data = index_data_or_path
    else:
        raise TypeError(f"Invalid type for index_data_or_path: {type(index_data_or_path)}")

    # Apply season filter to date_bool_mapping if requested
    if season == "SON":
        date_bool_mapping = {
            date: is_extreme
            for date, is_extreme in date_bool_mapping.items()
            if date.month in [9, 10, 11]
        }

    # Build extended extreme-date set (same rule used elsewhere)
    extended_dates = build_extended_dates(date_bool_mapping, days_prev_prec)

    # Compute prob extreme precipitation (marginal)
    original_extreme_dates = [d.replace(hour=0, minute=0, second=0, microsecond=0)
                              for d, flag in date_bool_mapping.items() if flag]
    prob_extreme = len(original_extreme_dates) / len(date_bool_mapping) if date_bool_mapping else 0

    # Find timestamps above large-scale threshold (index data may be dict or path)
    timestamps_above_large_scale = timestamps_above_threshold(
        index_data, threshold=threshold, start_year=start_year, end_year=end_year, perform_daily_mean=perform_daily_mean
    )

    # Filter tracks that overlap large-scale timestamps (with delta_time)
    filtered_tracks_with_large_scale = filter_tracks_by_timestamps(
        tracks, timestamps_above_large_scale, delta_time_track
    )

    # Tracks that also overlap the extended extreme dates (precip)
    filtered_tracks_with_large_scale_and_precipitation = tracks_warning_regions(
        filtered_tracks_with_large_scale, extended_dates
    )

    # Now compute counts
    computed_total_tracks = len(tracks)
    computed_tracks_with_large_scale = len(filtered_tracks_with_large_scale)
    computed_tracks_with_large_scale_and_precip = len(filtered_tracks_with_large_scale_and_precipitation)

    # If user passed numeric totals, log if there's disagreement (diagnostic)
    if tracks_all is not None and tracks_all != computed_total_tracks:
        logger.warning(f"Provided tracks_all ({tracks_all}) != recomputed total_tracks ({computed_total_tracks})")
    if tracks_with_large_scale is not None and tracks_with_large_scale != computed_tracks_with_large_scale:
        logger.warning(f"Provided tracks_with_large_scale ({tracks_with_large_scale}) != recomputed ({computed_tracks_with_large_scale})")
    if tracks_with_large_scale_and_precipitation is not None and tracks_with_large_scale_and_precipitation != computed_tracks_with_large_scale_and_precip:
        logger.warning(f"Provided tracks_with_large_scale_and_precipitation ({tracks_with_large_scale_and_precipitation}) != recomputed ({computed_tracks_with_large_scale_and_precip}).")

    # Conditional probability (use provided counts if available, since it is likely that recomputation has a bug!)
    prob_extreme_given_track_and_large_scale = (
        (tracks_with_large_scale_and_precipitation / tracks_with_large_scale)
        if tracks_with_large_scale else 0
    )

    # compute total_time_steps with ensemble_count
    all_ts = all_timestamps(index_data, start_year=start_year, end_year=end_year, perform_daily_mean=perform_daily_mean)
    total_time_steps = len(all_ts) * max(1, int(ensemble_count))
    p_event = tracks_with_large_scale_and_precipitation / total_time_steps if total_time_steps else 0

    # Logging
    logger.info(f"Total (recomputed) doublepass tracks with extreme precipitation and large scale: {computed_tracks_with_large_scale_and_precip}")
    logger.info(f"Total (recomputed) doublepass tracks with large scale: {computed_tracks_with_large_scale}")
    logger.info(f"Total (recomputed) doublepass tracks (i.e. simil vaia/florence): {computed_total_tracks}")
    logger.info(f"Probability of extreme precipitation (marginal): {prob_extreme:.4f}")
    logger.info(f"Probability of extreme precipitation given storm and large scale: {prob_extreme_given_track_and_large_scale:.4f}")
    logger.info(f"length all timestamps (single-member): {len(all_ts)}")
    logger.info(f"ensemble members count: {ensemble_count}")
    logger.info(f"total_time_steps (length * ensemble_count): {total_time_steps}")
    logger.info(f"Probability of event: {p_event:.6f}")

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

def concatenate_ensembles(ensembles_data):
    """
    Flatten multiple ensemble members into single combined structures and
    print diagnostic info on track counts per ensemble member.
    """

    combined_dates = {}
    combined_tracks = {}
    combined_index = {}

    next_track_id = 1
    ensemble_idx = 0

    # --- Diagnostic accumulators ---
    total_large_scale_all = 0
    total_large_scale_precip_all = 0
    total_tracks_all = 0

    for ens_data in ensembles_data:
        ensemble_idx += 1
        ens_name = ens_data.get("ens_name")

        dates = ens_data.get("dates", {})
        tracks = ens_data.get("tracks", {})
        idx = ens_data.get("index_path")

        # Read index file if it's a path
        if isinstance(idx, (str, bytes, os.PathLike)):
            try:
                index_data = read_index(idx)
            except Exception as e:
                logger.error(f"Failed to read index file {idx}: {e}")
                index_data = {}
        elif isinstance(idx, dict):
            index_data = idx
        else:
            index_data = {}

        # ---- Diagnostics per ensemble ----
        # Count large-scale timestamps
        timestamps_ls = timestamps_above_threshold(index_data, threshold=threshold, perform_daily_mean=perform_daily_mean)
        # Tracks associated with large-scale
        tracks_ls = filter_tracks_by_timestamps(tracks, timestamps_ls, delta_time_track)
        # Precipitation (dates where is_extreme == 1)
        extreme_dates = [d.replace(hour=0, minute=0, second=0, microsecond=0)
                         for d, flag in dates.items() if flag]
        extended_dates = set()
        for dt in extreme_dates:
            for i in range(days_prev_prec + 1):
                extended_dates.add(dt - timedelta(days=i))
        # Tracks overlapping both large-scale and extreme-precipitation days
        tracks_ls_precip = tracks_warning_regions(tracks_ls, extended_dates)

        total_tracks = len(tracks)
        total_ls = len(tracks_ls)
        total_ls_precip = len(tracks_ls_precip)

        total_tracks_all += total_tracks
        total_large_scale_all += total_ls
        total_large_scale_precip_all += total_ls_precip

        logger.info(
            f"[{ens_name}] tracks total={total_tracks}, "
            f"large-scale={total_ls}, "
            f"large-scale+precip={total_ls_precip}"
        )

        # --- Combine into master structures ---
        combined_dates.update(dates)

        for old_tid, track_info in tracks.items():
            new_tid = next_track_id
            next_track_id += 1
            header = track_info.get("header", {}).copy()
            header["_ORIGINAL_TRACK_ID"] = old_tid
            header["_ENSEMBLE_IDX"] = ensemble_idx
            combined_tracks[new_tid] = {
                "header": header,
                "data": list(track_info.get("data", []))
            }

        combined_index.update(index_data)

    # --- After loop: print combined stats ---
    logger.info("=============================================================")
    logger.info(f"Total ensembles concatenated: {ensemble_idx}")
    logger.info(f"Summed over ensembles: tracks={total_tracks_all}, "
                f"large-scale={total_large_scale_all}, "
                f"large-scale+precip={total_large_scale_precip_all}")
    logger.info("-------------------------------------------------------------")

    # Compute combined diagnostics again on concatenated data
    # (to check if it matches the sum)
    timestamps_ls_combined = timestamps_above_threshold(combined_index, threshold=threshold, perform_daily_mean=perform_daily_mean)
    tracks_ls_combined = filter_tracks_by_timestamps(combined_tracks, timestamps_ls_combined, delta_time_track)

    # Build combined extreme-date set
    combined_extreme_dates = [d.replace(hour=0, minute=0, second=0, microsecond=0)
                              for d, flag in combined_dates.items() if flag]
    extended_dates_combined = set()
    for dt in combined_extreme_dates:
        for i in range(days_prev_prec + 1):
            extended_dates_combined.add(dt - timedelta(days=i))
    tracks_ls_precip_combined = tracks_warning_regions(tracks_ls_combined, extended_dates_combined)

    logger.info(f"[COMBINED] tracks total={len(combined_tracks)}, "
                f"large-scale={len(tracks_ls_combined)}, "
                f"large-scale+precip={len(tracks_ls_precip_combined)}")
    logger.info("=============================================================")

    # Return combined structures
    ensemble_count = max(1, len(ensembles_data))
    return combined_dates, combined_tracks, combined_index, ensemble_count, total_tracks_all, total_large_scale_all, total_large_scale_precip_all



def plot_histogram_probabilities(result_data, output_dir, seas):
    """
    Plot histograms comparing ERA5, flattened historical, and flattened SSP245 probabilities.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    datasets = {
        "ERA5": [result_data["era5_prob"], result_data["era5_prob_given"], result_data["era5_p_event"]],
        "Historical (flattened)": [result_data["hist_prob"], result_data["hist_prob_given"], result_data["hist_p_event"]],
        "SSP245 (flattened)": [result_data["ssp_prob"], result_data["ssp_prob_given"], result_data["ssp_p_event"]],
    }

    labels = [
        "P(Extreme Precipitation)",
        "P(Extreme Precipitation | Storm, Large Scale)",
        "P(Event)"
    ]

    for i, label in enumerate(labels):
        plt.figure(figsize=(8, 6))
        bars = [probs[i] for probs in datasets.values()]
        plt.bar(list(datasets.keys()), bars, color=["black", "green", "orange"], alpha=0.7)
        plt.ylabel("Probability")
        plt.title(f"{label} - {seas}")
        plt.grid(True, axis="y", linestyle="--", alpha=0.4)
        plt.tight_layout()
        filename = f"histogram_{label.replace(' ', '_').replace('|','_')}.png"
        plt.savefig(os.path.join(output_dir, filename), dpi=300)
        plt.close()
        print(f"Saved histogram: {filename}")


def main():
    save_plot = True
    save_results_json = True
    print_track_counts = True
    print_txt_flattened = True
    compute_probabilities_bool = True

    result_file_json = "/home/ghinassi/pyTRACK-CMIP6/diagnostics/precipitation_diagnostics/json_file_probabilities/precipitation_probabilities_flattened.json"
    output_dir = "/home/ghinassi/work/track_plots/precipitation_extremes_flattened"
    output_file_txt = os.path.join("/home/ghinassi/work/track_plots/precipitation_extremes_flattened/precipitation_extreme_probabilities_flattened.txt")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # === Years for datasets ===
    year1_era5, year2_era5 = 1984, 2014
    year1_hist, year2_hist = 1984, 2014
    year1_ssp245, year2_ssp245 = 2070, 2100

    if not compute_probabilities_bool:
        print("Loading pre-computed probabilities from JSON file...")
        with open(result_file, "r") as f:
            result_data = json.load(f)
    else:
        print("Computing flattened probabilities...")

        # === ERA5 ===
        print(f"\nProcessing ERA5 ({year1_era5}-{year2_era5}), season: {seas}")
        era5_warning_file = "/home/ghinassi/work/ENCIRCLE_precipitation/output_precipitation_warning_regions/ERA5/ERA5_19500101_20241231_P99_direct_noaverage_italy_gridpoint.csv"
        era5_track_path = "/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue/"
        era5_dates = extract_date_bool_dict(era5_warning_file, is_excel=False)
        era5_dates = filter_by_year_range(era5_dates, year1_era5, year2_era5)
        era5_tracks = read_tracks(era5_track_path, ERA5_filtered_file)
        era5_tracks = filter_tracks_by_year_range(era5_tracks, year1_era5, year2_era5)
        index_path_ERA5 = "/home/ghinassi/work/similarity_pattern_index_pkl/index_pattern_ERA5.pkl"

        era5_prob, era5_prob_given, era5_p_event = compute_probabilities_ERA5(
            era5_dates, era5_tracks, index_path_ERA5,
            delta_time_track, days_prev_prec, year1_era5, year2_era5, season=seas
        )
        print(f"ERA5 done: P(extreme)={era5_prob:.4f}, P(extreme|storm,large scale)={era5_prob_given:.4f}, P(event)={era5_p_event:.4f}")

        # === CMIP6 Model ===
        model = "EC-Earth3"
        warning_region_path = "/home/ghinassi/work/ENCIRCLE_precipitation/output_precipitation_warning_regions"
        warning_pattern = "EC-Earth3_concatenated_hist+ssp245_*_19500101_20991231_P99_direct_noaverage_italy_gridpoint.xlsx"
        vaia_tracks_filename_hist = f"concatenated_tracks_firstlatpass39_firstlonpass4_firstrad3.5_secondlatpass45_secondlonpass10_secondrad3.5_gen_{year1_hist}-{year2_hist}.txt"
        vaia_tracks_filename_scen = f"concatenated_tracks_firstlatpass39_firstlonpass4_firstrad3.5_secondlatpass45_secondlonpass10_secondrad3.5_gen_{year1_ssp245}-{year2_ssp245}.txt"

        hist_ensembles_data, ssp_ensembles_data = [], []
        files = glob.glob(os.path.join(warning_region_path, warning_pattern))

        print(f"\nProcessing {model} model, found {len(files)} ensemble files.")
        for warning_file in files:
            ensemble = warning_file.split("_")[7]
            print(f"\nProcessing ensemble: {ensemble}")

            # === Historical ===
            hist_track_dir = f"/home/ghinassi/work/track_output/CMIP6/{model}/historical/{seas}/{ensemble}/psl/vaia_analogue"
            if os.path.isfile(os.path.join(hist_track_dir, vaia_tracks_filename_hist)):
                index_file = os.path.join(base_index_path, f"index_pattern_{model}_historical_{ensemble}.pkl")
                hist_dates = extract_date_bool_dict(warning_file, is_excel=True)
                hist_dates = filter_by_year_range(hist_dates, year1_hist, year2_hist)
                hist_tracks = read_tracks(hist_track_dir, vaia_tracks_filename_hist)
                hist_tracks = filter_tracks_by_year_range(hist_tracks, year1_hist, year2_hist)
                hist_ensembles_data.append({
                    "ens_name": ensemble,
                    "dates": hist_dates,
                    "tracks": hist_tracks,
                    "index_path": index_file       
                })

            # === SSP245 ===
            ssp_track_dir = f"/home/ghinassi/work/track_output/CMIP6/{model}/scenarioMIP/ssp245/{seas}/{ensemble}/psl/vaia_analogue"
            if os.path.isfile(os.path.join(ssp_track_dir, vaia_tracks_filename_scen)):
                index_file = os.path.join(base_index_path, f"index_pattern_{model}_scenarioMIP_ssp245_{ensemble}.pkl")
                ssp_dates = extract_date_bool_dict(warning_file, is_excel=True)
                ssp_dates = filter_by_year_range(ssp_dates, year1_ssp245, year2_ssp245)
                ssp_tracks = read_tracks(ssp_track_dir, vaia_tracks_filename_scen)
                ssp_tracks = filter_tracks_by_year_range(ssp_tracks, year1_ssp245, year2_ssp245)
                ssp_ensembles_data.append({
                    "ens_name": ensemble,
                    "dates": ssp_dates,
                    "tracks": ssp_tracks,
                    "index_path": index_file})
                
        # === Concatenate all ensemble members ===
        print("\nConcatenating all historical ensembles...")
        hist_dates_all, hist_tracks_all, hist_index_all, hist_ens_count, hist_total_tracks_all, hist_total_large_scale_all, hist_total_large_scale_precip_all = concatenate_ensembles(hist_ensembles_data)
        hist_prob, hist_prob_given, hist_p_event = compute_probabilities_flattened(
            hist_dates_all, hist_tracks_all, hist_index_all,
            hist_total_tracks_all, hist_total_large_scale_all, hist_total_large_scale_precip_all,
            delta_time_track, days_prev_prec, year1_hist, year2_hist, season=seas, ensemble_count=hist_ens_count
        )

        print("\nConcatenating all SSP245 ensembles...")
        ssp_dates_all, ssp_tracks_all, ssp_index_all, ssp_ens_count, ssp_total_tracks_all, ssp_total_large_scale_all, ssp_total_large_scale_precip_all = concatenate_ensembles(ssp_ensembles_data)
        ssp_prob, ssp_prob_given, ssp_p_event = compute_probabilities_flattened(
            ssp_dates_all, ssp_tracks_all, ssp_index_all,
            ssp_total_tracks_all, ssp_total_large_scale_all, ssp_total_large_scale_precip_all,
            delta_time_track, days_prev_prec, year1_ssp245, year2_ssp245, season=seas, ensemble_count=ssp_ens_count
        )

        result_data = {
            "era5_prob": era5_prob,
            "era5_prob_given": era5_prob_given,
            "era5_p_event": era5_p_event,
            "hist_prob": hist_prob,
            "hist_prob_given": hist_prob_given,
            "hist_p_event": hist_p_event,
            "ssp_prob": ssp_prob,
            "ssp_prob_given": ssp_prob_given,
            "ssp_p_event": ssp_p_event
        }

        # Save results in a json file
        if save_results_json:
            if not os.path.exists(os.path.dirname(result_file_json)):
                os.makedirs(os.path.dirname(result_file_json), exist_ok=True)
            with open(result_file_json, "w") as f:
                json.dump(result_data, f, indent=2)
            print(f"\nFlattened probability results saved to: {result_file_json}")

    # === Plotting ===
    if save_plot:
        plot_histogram_probabilities(result_data, output_dir, seas)

    # === Write summary TXT ===
    if print_txt_flattened:
        with open(output_file_txt, "w") as f:
            f.write("\nFlattened Precipitation Probabilities:\n")
            f.write(f"ERA5: P(extreme) = {result_data['era5_prob']:.4f}, "
                    f"P(extreme | storm, large scale) = {result_data['era5_prob_given']:.4f}, "
                    f"P(event) = {result_data['era5_p_event']:.4f}\n")
            f.write(f"Historical (flattened): P(extreme) = {result_data['hist_prob']:.4f}, "
                    f"P(extreme | storm, large scale) = {result_data['hist_prob_given']:.4f}, "
                    f"P(event) = {result_data['hist_p_event']:.4f}\n")
            f.write(f"SSP245 (flattened): P(extreme) = {result_data['ssp_prob']:.4f}, "
                    f"P(extreme | storm, large scale) = {result_data['ssp_prob_given']:.4f}, "
                    f"P(event) = {result_data['ssp_p_event']:.4f}\n")
        sys.__stdout__.write(f"Flattened probabilities written to {output_file_txt}\n")
        
    # === Print all info about total time steps, total timesteps above large scale and track counts summary for each ensemble  member ===
    # === Print and save track count summary for all ensemble members ===
    if print_track_counts:
        summary_lines = []
        summary_lines.append("\nTrack count summary (all ensemble members):")
        summary_lines.append("=" * 60)

        # --- ERA5 summary ---
        timestamps_ls_era5 = timestamps_above_threshold(index_path_ERA5, threshold=threshold,
                                                        start_year=year1_era5, end_year=year2_era5,
                                                        perform_daily_mean=perform_daily_mean)
        total_ts_era5 = len(all_timestamps(index_path_ERA5, start_year=year1_era5,
                                           end_year=year2_era5, perform_daily_mean=perform_daily_mean))
        large_scale_ts_era5 = len(timestamps_ls_era5)
        total_tracks_era5 = len(era5_tracks)
        large_scale_tracks_era5 = len(filter_tracks_by_timestamps(era5_tracks, timestamps_ls_era5, delta_time_track))
        # Ensure timestamps are aligned to the same format and granularity
        # Build extended dates (same rule used in compute functions)
        extended_dates = build_extended_dates(era5_dates, days_prev_prec)
        large_scale_precip_tracks = len(tracks_warning_regions(
        filter_tracks_by_timestamps(era5_tracks, timestamps_ls_era5, delta_time_track),
        extended_dates))
        
        # if logging info is selected print the starting date of the event with large scale and precipitation
        # ADD LOGGING INFO HERE
        logger.info(f"ERA5 large scale + precip tracks dates:")
        for track_id, track_info in tracks_warning_regions(
            filter_tracks_by_timestamps(era5_tracks, timestamps_ls_era5, delta_time_track),
            extended_dates
        ).items():
            dates_in_track = [datetime.strptime(point[0], "%Y%m%d%H") for point in track_info["data"]]
            logger.info(f"  Track ID {track_id}: Dates = {[date.strftime('%Y-%m-%d %H:%M') for date in dates_in_track]}")
    

        line = (f"ERA5 ({year1_era5}-{year2_era5}): total_ts={total_ts_era5}, "
                f"largescale_timesteps={large_scale_ts_era5}, total_tracks={total_tracks_era5}, "
                f"large_scale={large_scale_tracks_era5}, large+precip={large_scale_precip_tracks}")
        summary_lines.append(line)

        # --- Historical ensembles ---
        for i, ens_data in enumerate(hist_ensembles_data, 1):
            name = ens_data.get('ens_name', f"Historical {i}")
            idx = ens_data["index_path"]
            tracks = ens_data["tracks"]
            dates = ens_data["dates"]

            timestamps_ls = timestamps_above_threshold(idx, threshold=threshold, start_year=year1_hist, end_year=year2_hist, perform_daily_mean=perform_daily_mean)
            total_ts = len(all_timestamps(idx, start_year=year1_hist, end_year=year2_hist, perform_daily_mean=perform_daily_mean))
            large_scale_ts = len(timestamps_ls)
            total_tracks = len(tracks)
            large_scale_tracks = len(filter_tracks_by_timestamps(tracks, timestamps_ls, delta_time_track))
            extended_dates = build_extended_dates(dates, days_prev_prec)
            large_scale_precip_tracks = len(tracks_warning_regions(
                filter_tracks_by_timestamps(tracks, timestamps_ls, delta_time_track),
                extended_dates
))
            line = (f"Historical {name}: total_ts={total_ts}, largescale_timesteps={large_scale_ts}, "
                    f"total_tracks={total_tracks}, large_scale={large_scale_tracks}, "
                    f"large+precip={large_scale_precip_tracks}")
            summary_lines.append(line)

        # --- SSP245 ensembles ---
        for i, ens_data in enumerate(ssp_ensembles_data, 1):
            name = ens_data.get('ens_name', f"SSP245 {i}")
            idx = ens_data["index_path"]
            tracks = ens_data["tracks"]
            dates = ens_data["dates"]

            timestamps_ls = timestamps_above_threshold(idx, threshold=threshold, start_year=year1_ssp245, end_year=year2_ssp245, perform_daily_mean=perform_daily_mean)
            total_ts = len(all_timestamps(idx, start_year=year1_ssp245, end_year=year2_ssp245, perform_daily_mean=perform_daily_mean))
            large_scale_ts = len(timestamps_ls)
            total_tracks = len(tracks)
            large_scale_tracks = len(filter_tracks_by_timestamps(tracks, timestamps_ls, delta_time_track))
            extended_dates = build_extended_dates(dates, days_prev_prec)
            large_scale_precip_tracks = len(tracks_warning_regions(
                filter_tracks_by_timestamps(tracks, timestamps_ls, delta_time_track),
                extended_dates
))

            line = (f"ssp245 {name}: total_ts={total_ts}, largescale_timesteps={large_scale_ts}, "
                    f"total_tracks={total_tracks}, large_scale={large_scale_tracks}, "
                    f"large+precip={large_scale_precip_tracks}")
            summary_lines.append(line)

        # --- Print and save output ---
        print("\n".join(summary_lines))
        summary_path = os.path.join("/home/ghinassi/work/track_plots/risk_ratio_probabilities", "track_counts_summary.txt")
        with open(summary_path, "w") as f:
            f.write("\n".join(summary_lines))

        print(f"\nTrack count summary saved to: {summary_path}")


if __name__ == "__main__":
    main()


