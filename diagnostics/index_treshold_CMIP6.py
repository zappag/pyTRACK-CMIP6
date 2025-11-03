import os
import pickle
import pandas as pd
from datetime import datetime
import sys

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

"""
EC-Earth3 Cyclone Track Analysis Based on Similarity Pattern Index (SPI)

This script analyzes cyclone tracks from the EC-Earth3 model (CMIP6) and evaluates the probability 
of cyclone occurrence given a large-scale Z500 pattern similar to historical events (e.g., Vaia, Florence), 
quantified using a Similarity Pattern Index (SPI).

For each available ensemble member:
1. SPI data is loaded and resampled to daily means.
2. Days with SPI values above a specified threshold are identified.
3. Cyclone tracks are loaded and filtered to retain only those that occur on (or near) 
   high-SPI days.
4. A subset of analogue tracks (e.g., Vaia-like) is also filtered similarly.
5. Two probabilities are computed per ensemble:
   - P(pattern): Probability of observing a large-scale Z500 pattern similar to the target event.
   - P(storm | pattern): Probability of observing a storm (matching analogue) given the large-scale pattern.
"""

model_name = "EC-Earth3"
expn = "scenarioMIP"  # or "historical"
expt = "ssp245"       # used only if expn == "scenarioMIP"

# Optional: specify a year range to restrict the analysis
start_year = 2070
end_year = 2100

# Handle experiment label
expn_label = f"{expn}_{expt}" if expn == "scenarioMIP" else expn

# Start logging to file and console
log_file_path = "/home/ghinassi/work/track_plots/summary_index_probability/"
log_filename = f"storm_givenlargescale_pattern_{model_name}_{expn_label}_{start_year}_{end_year}.txt"
sys.stdout = Logger(os.path.join(log_file_path, log_filename))

# Base paths
base_index_path = "/home/ghinassi/work/similarity_pattern_index_pkl/"
base_tracks_path = f"/home/ghinassi/work/track_output/CMIP6/{model_name}/"
base_tracks_path += f"scenarioMIP/ssp245/SON/" if expn == "scenarioMIP" else "historical/SON/"

vaia_tracks_filename = "concatenated_tracks_lat38_lon4_rad4_lat45_lon8_rad4.txt"

ens_list = [
    "r2i1p1f1", "r7i1p1f1", "r10i1p1f1", "r12i1p1f1", "r14i1p1f1", 
    "r16i1p1f1", "r17i1p1f1", "r18i1p1f1", "r19i1p1f1", "r20i1p1f1", 
    "r21i1p1f1", "r22i1p1f1", "r23i1p1f1", "r24i1p1f1", "r25i1p1f1"
]

def convert_lon(lon):
    return lon - 360 if lon > 180 else lon

def convert_lon180_360(lon):
    return lon + 360 if lon < 0 else lon

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

def get_all_timestamps(index_file, start_year=None, end_year=None):
    with open(index_file, 'rb') as file:
        data = pickle.load(file)
    df = pd.DataFrame(list(data.items()), columns=['timestamp', 'index_value'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    if start_year is not None and end_year is not None:
        df = df[(df['timestamp'].dt.year >= start_year) & (df['timestamp'].dt.year <= end_year)]
    daily_mean_df = df.resample('D', on='timestamp').mean()
    return [(ts.strftime('%Y%m%d%H'), val) for ts, val in daily_mean_df.itertuples()]

def get_timestamps_above_threshold(index_file, threshold=0.9, start_year=None, end_year=None):
    with open(index_file, 'rb') as file:
        data = pickle.load(file)
    df = pd.DataFrame(list(data.items()), columns=['timestamp', 'index_value'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    if start_year is not None and end_year is not None:
        df = df[(df['timestamp'].dt.year >= start_year) & (df['timestamp'].dt.year <= end_year)]
    daily_mean_df = df.resample('D', on='timestamp').mean()
    return [(ts.strftime('%Y%m%d%H'), val) for ts, val in daily_mean_df.itertuples() if val > threshold]

def filter_tracks_by_threshold(tracks, timestamps_above_threshold, delta_time=0):
    timestamps_set = set()
    for ts, _ in timestamps_above_threshold:
        base_ts = datetime.strptime(ts, '%Y%m%d%H')
        timestamps_set.add(ts)
        if delta_time > 0:
            shifted_ts = base_ts + pd.Timedelta(hours=delta_time)
            timestamps_set.add(shifted_ts.strftime('%Y%m%d%H'))
    return {
        track_id: info
        for track_id, info in tracks.items()
        if any(point[0] in timestamps_set for point in info["data"])
    }

### === MAIN LOOP FOR ENSEMBLES === ###
threshold = 0.9
delta_time = 48

ensemble_prob_stats = []

for ens in ens_list:
    print(f"\nProcessing ensemble: {ens}")
    index_file = os.path.join(base_index_path, f"index_pattern_{model_name}_{expn_label}_{ens}.pkl")
    tracks_dir = os.path.join(base_tracks_path, ens, "psl/total_tracks/")

    try:
        timestamps_above = get_timestamps_above_threshold(index_file, threshold, start_year, end_year)
        total_timestamps = get_all_timestamps(index_file, start_year, end_year)

        concatenated_tracks_filename = f"concatenated_tracks_{ens}.txt"
        ec_earth_tracks = read_tracks(tracks_dir, filename=concatenated_tracks_filename)
        vaia_tracks = read_tracks(os.path.join(base_tracks_path, ens, "psl/vaia_analogue"), filename=vaia_tracks_filename)

        filtered_tracks = filter_tracks_by_threshold(ec_earth_tracks, timestamps_above, delta_time)
        filtered_vaia_tracks = filter_tracks_by_threshold(vaia_tracks, timestamps_above, delta_time)

        prob_large_scale = len(timestamps_above) / len(total_timestamps)
        prob_storm_given_pattern = len(filtered_vaia_tracks) / len(timestamps_above) if timestamps_above else 0

        print(f"Timestamps above threshold: {len(timestamps_above)}")
        print(f"Total timestamps: {len(total_timestamps)}")
        print(f"Probability of large-scale pattern: {prob_large_scale:.3f}")
        print(f"Matching Vaia-like tracks: {len(filtered_vaia_tracks)}")
        print(f"Probability of storm given pattern: {prob_storm_given_pattern:.3f}")

        ensemble_prob_stats.append({
            "model": model_name,
            "experiment": expn_label,
            "ensemble_member": ens,
            "start_year": start_year,
            "end_year": end_year,
            "threshold": threshold,
            "P(pattern)": prob_large_scale,
            "P(storm|pattern)": prob_storm_given_pattern,
            "num_pattern_days": len(timestamps_above),
            "num_storm_days": len(filtered_vaia_tracks),
        })

    except FileNotFoundError as e:
        print(f"Missing data for ensemble {ens}: {e}")
        continue

# Optionally: summarize or average across ensembles
mean_prob_pattern = sum(d["P(pattern)"] for d in ensemble_prob_stats) / len(ensemble_prob_stats)
mean_prob_storm = sum(d["P(storm|pattern)"] for d in ensemble_prob_stats) / len(ensemble_prob_stats)

print("\n=== SUMMARY ===")
print(f"model: {model_name}", f"experiment: {expn_label}", f"start_year: {start_year}", f"end_year: {end_year}")
print(f"threshold: {threshold}")
print(f"Average probability of pattern across ensembles: {mean_prob_pattern:.3f}")
print(f"Average probability of storm given pattern across ensembles: {mean_prob_storm:.3f}")

