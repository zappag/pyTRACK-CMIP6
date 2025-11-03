import precip_in_warning_regions_GP as pwr
import os
from datetime import datetime, timedelta
import pandas as pd
import glob

model= "EC-Earth3"
exp = "historical" # exps can be: historical or scenarioMIP
exp_name = "ssp245" # if exp is scenarioMIP, specify the experiment name
seas = "SON" # seasons can be: DJF, MAM, JJA, SON

warning_region_path = "/home/ghinassi/work/ENCIRCLE_precipitation/output_precipitation_warning_regions"
warning_region_pattern = "EC-Earth3_concatenated_hist+ssp245_*_19500101_20991231_P99_direct_noaverage_italy_gridpoint.xlsx"

if exp == "historical":
    filtered_tracks_root = f"/home/ghinassi/work/track_output/CMIP6/{model}/{exp}/{seas}/"
elif exp == "scenarioMIP":
    filtered_tracks_root = f"/home/ghinassi/work/track_output/CMIP6/{model}/{exp}/{exp_name}/{seas}/"
filtered_tracks_filename = "concatenated_tracks_lat38_lon4_rad4_lat45_lon8_rad4.txt"

def extract_date_bool_dict(filepath):
    df = pd.read_excel(filepath)

    # Ensure the first and last columns are selected
    first_col = df.columns[0]
    last_col = df.columns[-1]

    # Exclude the last row since the last entry is not a datetime
    df = df.iloc[:-1]
    df[first_col] = pd.to_datetime(df[first_col])
    df[last_col] = df[last_col].astype(int)

    return dict(zip(df[first_col], df[last_col]))

def convert_lon(lon):
    return lon - 360 if lon > 180 else lon

def read_tracks(track_dir, filename=None):
    tracks = {}
    if not os.path.isdir(track_dir):
        return tracks  # Skip if directory doesn't exist

    full_path = os.path.join(track_dir, filename)
    if not os.path.isfile(full_path):
        return tracks  # Skip if file doesn't exist

    with open(full_path, "r") as file:
        track_id = None
        track_data = []
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

    return tracks

def tracks_warning_regions(tracks, timestamps_set):
    filtered_tracks = {
        track_id: track_info
        for track_id, track_info in tracks.items()
        if any(
            datetime.strptime(point[0], "%Y%m%d%H").replace(hour=0, minute=0, second=0, microsecond=0) in timestamps_set
            for point in track_info["data"]
        )
    }
    return filtered_tracks

if __name__ == "__main__":
    warning_files = glob.glob(os.path.join(warning_region_path, warning_region_pattern))
    days_prev = 2

    for warning_file in warning_files:
        ensemble_member = warning_file.split("_")[7]  # Extract ens member name from file name
        track_dir = os.path.join(filtered_tracks_root, ensemble_member, "psl", "vaia_analogue")

        print(f"\nProcessing ensemble member: {ensemble_member}")

        date_bool_mapping = extract_date_bool_dict(warning_file)

        original_extreme_dates = [
            date.replace(hour=0, minute=0, second=0, microsecond=0)
            for date, is_extreme in date_bool_mapping.items() if is_extreme
        ]

        dates_with_extreme = set()
        for date in original_extreme_dates:
            for i in range(days_prev + 1):
                dates_with_extreme.add(date - timedelta(days=i))

        tracks = read_tracks(track_dir, filtered_tracks_filename)
        tracks_with_extreme = tracks_warning_regions(tracks, dates_with_extreme)
        print(f"Model: {model}, Experiment: {exp}, Season: {seas}")
        print(f"Ensemble member: {ensemble_member}")
        print(f"Found {len(tracks)} tracks in the directory: {track_dir}")
        print(f"Found {len(tracks_with_extreme)} tracks with extreme precipitation events.")

        total_time_steps = len(date_bool_mapping)
        len_extreme = len(original_extreme_dates)
        prob_extreme = len_extreme / total_time_steps if total_time_steps > 0 else 0
        print(f"Probability of extreme precipitation: {prob_extreme:.4f}")

        total_tracks = len(tracks)
        prob_extreme_given_track = len(tracks_with_extreme) / total_tracks if total_tracks > 0 else 0
        print(f"Probability of extreme precipitation given a Florence/Vaia pass track: {prob_extreme_given_track:.4f}")
