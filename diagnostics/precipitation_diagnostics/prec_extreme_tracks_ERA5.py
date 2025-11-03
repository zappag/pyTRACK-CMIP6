import precip_in_warning_regions_GP as pwr
import os
from datetime import datetime
from datetime import timedelta
import pandas as pd

"""
This code opens the extreme precipitation warning region excel file
and for each date in which a precipitation extreme is found in the largest warning region (>50.000 km2)
it checks if a track exists in the ERA5 tracks directory at the same time
between the vaia/florence filtered tracks.
It then prints the track ID and the date of the extreme precipitation event.
"""

warning_region_file = "/home/ghinassi/precipitation_diagnostics/ERA5/ERA5_19500101_20241231_P99_direct_noaverage_italy_gridpoint.csv"

# Path to the filtered tracks directory from ERA5
filtered_tracks_path="/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue/"
filtered_tracks_filename = "concatenated_tracks_lat38_lon4_rad4_lat45_lon8_rad4_1940-2024.txt"

def extract_date_bool_dict(filepath):
    """
    Reads an Excel file and extracts a dictionary mapping dates (from the first column)
    to boolean values (from the last column).

    :param filepath: Path to the Excel file
    :return: Dictionary with date keys and boolean values
    """
    df = pd.read_csv(filepath)

    # Ensure the first and last columns are selected
    first_col = df.columns[0]
    last_col = df.columns[-1]

    # Exclude the last row since the last entry is not a datetime
    df = df.iloc[:-1]
    df[first_col] = pd.to_datetime(df[first_col])

    # Convert the last column to integer (0/1) if not already
    df[last_col] = df[last_col].astype(int)

    # Create dictionary
    date_bool_dict = dict(zip(df[first_col], df[last_col]))

    return date_bool_dict

def convert_lon(lon):
    return lon - 360 if lon > 180 else lon

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

def tracks_warning_regions(ERA5_tracks, timestamps_warning_regions):

    # Extract only the timestamps from the threshold data for faster lookup
    timestamps_set = set(timestamps_warning_regions)
    
    #drop the time to compare only the data until the day
    

    # Filter tracks that have at least one matching date (ignore time, compare only the day)
    filtered_tracks = {
        track_id: track_info
        for track_id, track_info in ERA5_tracks.items()
        if any(
            datetime.strptime(point[0], "%Y%m%d%H").replace(hour=0, minute=0, second=0, microsecond=0) in timestamps_set
            for point in track_info["data"]
        )
    }

    return filtered_tracks


# Example usage
if __name__ == "__main__":
    date_bool_mapping = extract_date_bool_dict(warning_region_file)
    days_prev = 2  # Number of days before the extreme event to consider

    # Select only the dates with extreme precipitation
    original_extreme_dates = [
        date.replace(hour=0, minute=0, second=0, microsecond=0)
        for date, is_extreme in date_bool_mapping.items() if is_extreme
    ]

    # Expand to include days from (date - days_prev) through (date)
    dates_with_extreme = set()
    for date in original_extreme_dates:
        for i in range(days_prev + 1):
            day = (date - timedelta(days=i))
            dates_with_extreme.add(day)


    

    #now check if any of the dates_with_extreme matches the double pass track dates
    ERA5_tracks_vaiapass = read_tracks(filtered_tracks_path, filtered_tracks_filename)
    tracks_with_extreme = tracks_warning_regions(ERA5_tracks_vaiapass, dates_with_extreme)
    print(f"Found {len(tracks_with_extreme)} tracks with extreme precipitation events.")
    """
    # Print the track IDs and dates of extreme precipitation events
    for track_id, track_info in tracks_with_extreme.items():
        for point in track_info["data"]:
            date = datetime.strptime(point[0], "%Y%m%d%H").replace(hour=0, minute=0, second=0, microsecond=0)
            if date in dates_with_extreme:
                print(f"Track ID: {track_id}, Date: {date.strftime('%Y-%m-%d')}")
    """
    # now compute the probability of extreme precipitation in ERA5 data first
    # as the total time steps in the original extreme dates divided by the total number of time steps in the ERA5 data
    total_time_steps = len(date_bool_mapping)
    extreme_dates = [date for date, is_extreme in date_bool_mapping.items() if is_extreme]
    len_extreme = len(extreme_dates)
    if total_time_steps == 0:
        prob_extreme = 0
    else:
        prob_extreme = len_extreme / total_time_steps
    print(f"Probability of extreme precipitation in ERA5 data: {prob_extreme:.4f}")
    
    #second the probability of extreme precipitation over italy given a vailapass track
    total_tracks = len(ERA5_tracks_vaiapass)
    total_tracks_with_extreme = len(tracks_with_extreme)
    if total_tracks == 0:
        prob_extreme_given_track = 0
    else:
        prob_extreme_given_track = total_tracks_with_extreme / total_tracks
    print(f"Probability of extreme precipitation given a VaiaPass track: {prob_extreme_given_track:.4f}")