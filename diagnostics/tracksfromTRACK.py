import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature

ERA5_track_dir = "/home/zappa/work_big/TRACK_tracks/ERA5/ERA5_VOR850_1hr_oct-mar20182019_DET/dates"
ERA5_mslp_dir = "/home/zappa/work/ERA5/hourly/mean_sea_level_pressure/6hrs/"
mslp_filename = "ERA5_mean_sea_level_pressure_6hrs_full_sfc_2018_70_-50_10_55.nc"

plotdir= "/home/ghinassi/work/diagnostics/plots/tracks_all/"

def read_ERA5_tracks(ERA5_track_dir):
    tracks = {}
    
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
                    #print("Track ID:", track_id)
                    continue
                elif line.startswith("POINT_NUM"):
                    num_points = int(line.split()[1])
                    #print("Number of points:", num_points)
                    continue
                elif line:
                    data = line.split()
                    date = data[0]
                    lon = float(data[1])
                    lat = float(data[2])
                    track_data.append((date, lon, lat))

                if len(track_data) == num_points:
                    tracks[track_id] = {
                        "header": {
                            "TRACK_ID": track_id,
                            "START_TIME": data[0],
                            "POINT_NUM": num_points
                        },
                        "data": track_data
                    }
                    #print("Header:", tracks[track_id]["header"])
                    #print("Data (lon, lat):", [(lon, lat) for _, lon, lat in track_data])
                    track_id = None
                    track_data = []
    
    return tracks

def filter_tracks(tracks):
    filtered_tracks = {}
    
    for track_id, track_data in tracks.items():
        header = track_data["header"]
        data = track_data["data"]
        
        filtered_data = [(date, lon, lat) for date, lon, lat in data if date[-2:] in ["00", "06", "12", "18"]]
        
        if filtered_data:
            filtered_tracks[track_id] = {
                "header": header,
                "data": filtered_data
            }
    
    return filtered_tracks


def plot_tracks(tracks, plotdir, startdate=None, enddate=None, lat1=None, lat2=None, lon1=None, lon2=None):
    for track_id, track_data in tracks.items():
        header = track_data["header"]
        data = track_data["data"]
        
        # Extract lon and lat values from track data
        lon_values = [lon for _, lon, _ in data]
        lat_values = [lat for _, _, lat in data]

        # Create a PlateCarree projection
        projection = ccrs.PlateCarree()
        
        # Create a figure and axes with PlateCarree projection
        fig, ax = plt.subplots(subplot_kw={'projection': projection})

        # Filter tracks based on startdate and enddate
        if startdate and enddate:
            filtered_data = [(date, lon, lat) for date, lon, lat in data if pd.to_datetime(startdate, format="%Y%m%d%H").date() <= pd.to_datetime(date, format="%Y%m%d%H").date() <= pd.to_datetime(enddate, format="%Y%m%d%H").date()]
            lon_values = [lon for _, lon, _ in filtered_data]
            lat_values = [lat for _, _, lat in filtered_data]
        else:
            filtered_data = data
        
        # Filter tracks based on lat1, lat2, lon1, lon2
        if lat1 and lat2 and lon1 and lon2:
            filtered_data = [(date, lon, lat) for date, lon, lat in data if lat1 <= lat <= lat2 and lon1 <= lon <= lon2]
            lon_values = [lon for _, lon, _ in filtered_data]
            lat_values = [lat for _, _, lat in filtered_data]
        else:
            filtered_data = data

        # Plot track as scatter points if the filtered data is not empty
        if filtered_data:
            ax.scatter(lon_values, lat_values, color="black",
                        s=15,
                        linewidths=0.5,
                        marker=".",
                        alpha=0.8,
                        transform=projection)

            # Add latitude and longitude ticks
            ax.set_xticks(range(-180, 181, 30), crs=projection)
            ax.set_yticks(range(-90, 91, 10), crs=projection)

            if lat1 and lat2 and lon1 and lon2:
                ax.set_extent([lon1, lon2, lat2, lat1], crs=projection)

            # Add labels
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")

            # Add coastlines and continents
            ax.add_feature(cfeature.LAND, color='lightgrey')

            ax.set_title("Track ID: {}, Start Time: {}".format(header["TRACK_ID"], header["START_TIME"]))
            
            # Show plot
            plt.savefig(plotdir + "track_{}.png".format(header["START_TIME"]))
            print("saved plot for track ID: ", header["TRACK_ID"], " and start time: ", header["START_TIME"])

            plt.close()

def plot_mslp(ERA5_mslp_dir, mslp_filename, plotdir, startdate=None, enddate=None):
    # Read the ERA5 mean sea level pressure data
    mslp_data = xr.open_dataset(os.path.join(ERA5_mslp_dir, mslp_filename))

    # Extract the required variables
    lon_values = mslp_data["lon"]
    lat_values = mslp_data["lat"]
    mslp_values = mslp_data["MSL"]
    time_values = mslp_data["time"]

    # Create a PlateCarree projection
    projection = ccrs.PlateCarree()

    for t in range(len(time_values)):
       
        # Create a figure and axes with PlateCarree projection
        fig, ax = plt.subplots(subplot_kw={'projection': projection})
        
        # Plot the mslp values as a contour plot
        contour = ax.contour(lon_values, lat_values, mslp_values[t,:,:]/100, levels=10, cmap="coolwarm", transform=projection)
        
        # Add colorbar
        cbar = plt.colorbar(contour)
        cbar.set_label("Mean Sea Level Pressure (hPa)")
        
        # Add latitude and longitude ticks
        ax.set_xticks(range(-180, 181, 30), crs=projection)
        ax.set_yticks(range(-90, 91, 30), crs=projection)
        ax.set_extent([-10, 30, 55, 30], crs=projection)
        # Add labels
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        
        # Add coastlines and continents
        ax.add_feature(cfeature.LAND, color='lightgrey')
        
        # Save the plot
        plt.savefig(plotdir + "mslp_plot_{}.png".format(time_values[t].values))
        print("saved plot for time: ", time_values[t].values)
        plt.close()


tracks = read_ERA5_tracks(ERA5_track_dir)

#tracks = filter_tracks(tracks)

plot_tracks(tracks, plotdir) #, startdate="2018102600", enddate="2018110400", lat1=30, lat2=55, lon1=-10, lon2=30)
#plot_mslp(ERA5_mslp_dir, mslp_filename, plotdir, startdate="2018102600", enddate="2018110400")

#mslp plot + tutti i timestamp dei tracks
