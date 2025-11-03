import os
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# this code reads the filtered tracks after the execution of the script pass_trajectories.sh.
# The tracks are then plotted on a map.

var="msl"
seas="SON"

# dir with the vaia track to use as reference

ERA5_track_dir_vaia = f"/home/ghinassi/work/track_output/ERA5/SON/{var}/NH_ERA5_msl_6hr_2018_SON/dates/"
ERA5_track_vaia_filename = "ff_trs_neg.vaiagen_latgen38_longen4_radgen4_vaiapass_latpas45_lonpas8_radpas2"

# dir with florence track to use as reference
ERA5_track_dir_florence = f"/home/ghinassi/work/track_output/ERA5/SON/{var}/NH_ERA5_msl_6hr_1966_SON/dates/"
ERA5_track_florence_filename = "ff_trs_neg.vaiapass_lat38_lon4_rad4_vaiapass_lat45_lon10_rad2"

# other vaia analogous tracks to plot
ERA5_track_dir_vaia_analogue = f"/home/ghinassi/work/track_output/ERA5/{seas}/{var}/vaia_analogue/"
concatenated_tracks_filename = "concatenated_tracks_firstlatpass38_firstlonpass4_firstrad4_secondlatpass45_secondlonpass10_secondrad2_1940-2024.txt"

plotdir= "/home/ghinassi/work/track_plots/vaia_analogue"

def read_ERA5_tracks(ERA5_track_dir, filename=None):
    
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
                    #print("Track ID:", track_id)
                    start_time = int(line.split()[-1])
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
                            "START_TIME": start_time,
                            "POINT_NUM": num_points
                        },
                        "data": track_data
                    }
                    #print("Header:", tracks[track_id]["header"])
                    #print("Data (lon, lat):", [(lon, lat) for _, lon, lat in track_data])
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


def plot_tracks(track_ref, alltracks, plotdir, lat1=None, lat2=None, lon1=None, lon2=None, latgen=None, longen=None, radgen=None, latpas=None, lonpas=None, radpas=None, double_pass=False):
    for track_id, track_data in track_ref.items():
        header_ref = track_data["header"]
        data_ref = track_data["data"]
        
        # Extract lon and lat values from track data
        lon_values_ref = [(lon + 180) % 360 - 180 for _, lon, _ in data_ref]
        lat_values_ref = [lat for _, _, lat in data_ref]

        # Create a PlateCarree projection
        projection = ccrs.PlateCarree()
        
        # Create a figure and axes with PlateCarree projection
        fig, ax = plt.subplots(subplot_kw={'projection': projection})

        # Plot the trajectory as a line segment
        ax.plot(lon_values_ref, lat_values_ref, color="black",
                linewidth=2,
                transform=projection,
                label="Vaia")
        
        if alltracks:
            
            for track_id, track_data in alltracks.items():
                header = track_data["header"]
                data = track_data["data"]
                
                # Extract lon and lat values from track data
                lon_values = [(lon + 180) % 360 - 180 for _, lon, _ in data]
                lat_values = [lat for _, _, lat in data]
                
                # Plot the trajectory as a line segment with different shades of gray
                gray_shades = ['#808080', '#A9A9A9', '#C0C0C0', '#D3D3D3', '#DCDCDC']
                color = gray_shades[track_id % len(gray_shades)]
                ax.plot(lon_values, lat_values,
                        linewidth=0.4,
                        color=color,
                        transform=projection)
                
        # Add latitude and longitude ticks
        ax.set_xticks(range(-180, 181, 30), crs=projection)
        ax.set_yticks(range(-90, 91, 10), crs=projection)

        # add genesis circle and passage circles as polygons
        if latgen and longen and radgen and double_pass==False:
            print("adding genesis circle at lat: {}, lon: {}, rad: {}".format(latgen, longen, radgen))
            circle = plt.Circle((longen, latgen), radgen, color='red', fill=False, transform=ccrs.PlateCarree(), label="Genesis")
            ax.add_patch(circle)
        if latgen and longen and radgen and double_pass:
            print("adding passage circle at lat: {}, lon: {}, rad: {}".format(latgen, longen, radgen))
            circle = plt.Circle((longen, latgen), radgen, color='red', fill=False, transform=ccrs.PlateCarree(), label="Pass 1")
            ax.add_patch(circle)
        if latpas and lonpas and radpas:
            print("adding passage circle at lat: {}, lon: {}, rad: {}".format(latpas, lonpas, radpas))
            circle = plt.Circle((lonpas, latpas), radpas, color='blue', fill=False, transform=ccrs.PlateCarree(), label="Pass 2")
            ax.add_patch(circle)

        if lat1 and lat2 and lon1 and lon2:
            ax.set_extent([lon1, lon2, lat2, lat1], crs=projection)

        # Add labels
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

        # Add coastlines and continents
        ax.add_feature(cfeature.LAND, color="bisque")
        # Add legend
        ax.legend()

        if double_pass:
            ax.set_title("Double Pass tracks (Track var: {}, - Seas: {} - ERA5)".format(var, seas))
            filename = f"alltracks_vaiaanalogue_ERA5_{var}_{seas}_firstlatpass{latgen}_firstlonpass{longen}_firstrad{radgen}_secondlatpass{latpas}_secondlonpass{lonpas}_secondrad{radpas}.png"
        else:
            ax.set_title("Ref: Vaia (Var: {}, Track ID: {}, Start Time: {}) - Seas: {}".format(var, header_ref["TRACK_ID"], header_ref["START_TIME"], seas))
            filename = f"alltracks_vaiaanalogue_ERA5_{var}_{seas}_latgen{latgen}_longen{longen}_radgen{radgen}_latpas{latpas}_lonpas{lonpas}_radpas{radpas}.png"
        
        # Create the plot directory if it doesn't exist
        os.makedirs(plotdir, exist_ok=True)
        
        # Save plot
        plt.savefig(os.path.join(plotdir, filename))
        print("saved plot named: ", os.path.join(plotdir, filename))

        plt.close()
        
def plot_florence_and_vaia(track_ref1, track_ref2, alltracks, plotdir, lat1=None, lat2=None, lon1=None, lon2=None, latgen=None, longen=None, radgen=None, latpas=None, lonpas=None, radpas=None):
    
    # Create a PlateCarree projection
    projection = ccrs.PlateCarree()
    
    # Create a figure and axes with PlateCarree projection
    fig, ax = plt.subplots(subplot_kw={'projection': projection}, figsize=(10, 6))

    # Plot Florence track (ref track) in black
    for track_id, track_data in track_ref1.items():
        data_ref = track_data["data"]
        
        # Extract lon and lat values from track data
        lon_values_ref = [(lon + 180) % 360 - 180 for _, lon, _ in data_ref]
        lat_values_ref = [lat for _, _, lat in data_ref]

        # Plot the trajectory as a line segment
        ax.plot(lon_values_ref, lat_values_ref, color="black",
                linewidth=2,
                transform=projection,
                label="Florence")
        
    # Plot Vaia track in dark grey
    for track_id, track_data in track_ref2.items():
        data_ref = track_data["data"]
        
        # Extract lon and lat values from track data
        lon_values_ref = [(lon + 180) % 360 - 180 for _, lon, _ in data_ref]
        lat_values_ref = [lat for _, _, lat in data_ref]

        # Plot the trajectory as a line segment
        ax.plot(lon_values_ref, lat_values_ref, color="darkgrey",
                linewidth=2,
                transform=projection,
                label="Vaia")
            
    # Plot all other tracks with different shades of gray
    if alltracks:
        for track_id, track_data in alltracks.items():
            data = track_data["data"]
            
            # Extract lon and lat values from track data
            lon_values = [(lon + 180) % 360 - 180 for _, lon, _ in data]
            lat_values = [lat for _, _, lat in data]
            
            # Plot the trajectory as a line segment with different shades of gray
            gray_shades = ['#808080', '#A9A9A9', '#C0C0C0', '#D3D3D3', '#DCDCDC']
            color = gray_shades[track_id % len(gray_shades)]
            ax.plot(lon_values, lat_values,
                    linewidth=0.4,
                    color=color,
                    transform=projection)
            
    # Add passage circles as polygons
    if latgen and longen and radgen:
        print("adding passage circle at lat: {}, lon: {}, rad: {}".format(latgen, longen, radgen))
        circle = plt.Circle((longen, latgen), radgen, color='red', fill=False, transform=ccrs.PlateCarree(), label="Pass 1")
        ax.add_patch(circle)
    if latpas and lonpas and radpas:
        print("adding passage circle at lat: {}, lon: {}, rad: {}".format(latpas, lonpas, radpas))
        circle = plt.Circle((lonpas, latpas), radpas, color='blue', fill=False, transform=ccrs.PlateCarree(), label="Pass 2")
        ax.add_patch(circle)


    # Add latitude and longitude ticks
    ax.set_xticks(range(-180, 181, 30), crs=projection)
    ax.set_yticks(range(-90, 91, 10), crs=projection)
    
    # Set the map extent if boundaries are provided
    if lat1 and lat2 and lon1 and lon2:
        ax.set_extent([lon1, lon2, lat1, lat2], crs=projection)

    # Add labels
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Add coastlines and continents
    ax.add_feature(cfeature.LAND, color="bisque")
    
    # Add legend
    ax.legend()

    # Add title
    ax.set_title("Double Pass tracks (Track var: {}, - Seas: {} - ERA5)".format(var, seas))
    
    # Create the plot directory if it doesn't exist
    os.makedirs(plotdir, exist_ok=True)
    
    # Save plot
    filename = f"alltracks_florence_ERA5_{var}_{seas}_firstlatpass{latgen}_firstlonpass{longen}_firstrad{radgen}_secondlatpass{latpas}_secondlonpass{lonpas}_secondrad{radpas}.png"
    plt.savefig(os.path.join(plotdir, filename))
    print("saved plot named: ", os.path.join(plotdir, filename))

    plt.close()
        
def plot_track_density(track_ref, alltracks, plotdir, lat1=None, lat2=None, lon1=None, lon2=None):
    # plot track density of Vaia-like filtered tracks
    for track_id, track_data in track_ref.items():
        header_ref = track_data["header"]
        data_ref = track_data["data"]
        
        # Extract lon and lat values from track data
        lon_values_ref = [(lon + 180) % 360 - 180 for _, lon, _ in data_ref]
        lat_values_ref = [lat for _, _, lat in data_ref]

        # Create a PlateCarree projection
        projection = ccrs.PlateCarree()
        
        # Create a figure and axes with PlateCarree projection
        fig, ax = plt.subplots(subplot_kw={'projection': projection}, figsize=(10, 6))

        # Plot the reference trajectory as a line segment (Vaia track)
        ax.plot(lon_values_ref, lat_values_ref, color="black",
                linewidth=1.5,
                transform=projection,
                label="Vaia")
        
        # Handle all tracks for density plotting
        if alltracks:
            # Collect all longitude and latitude values for KDE
            all_lon_values, all_lat_values = [], []
            for track_id, track_data in alltracks.items():
                header = track_data["header"]
                data = track_data["data"]
                
                # Extract lon and lat values from track data
                all_lon_values += [(lon + 180) % 360 - 180 for _, lon, _ in data]
                all_lat_values += [lat for _, _, lat in data]

            # Perform KDE to get a smooth density field
            xy = np.vstack([all_lon_values, all_lat_values])
            kde = gaussian_kde(xy, bw_method=0.1)  # Bandwidth adjustment for smoothness
            
            # Create grid for evaluation
            lon_grid, lat_grid = np.meshgrid(np.arange(lon1, lon2, 0.05),
                                             np.arange(lat1, lat2, 0.05))
            
            # Evaluate KDE on the grid
            density = kde(np.vstack([lon_grid.ravel(), lat_grid.ravel()])).reshape(lon_grid.shape)

            # Plot the density as a smooth continuous field
            c = ax.pcolormesh(lon_grid, lat_grid, density, shading='auto', cmap='viridis', alpha=0.6, transform=projection)
            
            # Add colorbar to show density scale
            cbar = plt.colorbar(c, ax=ax, orientation='vertical', pad=0.02, label="Track Density")

        # Add latitude and longitude ticks
        ax.set_xticks(range(-180, 181, 30), crs=projection)
        ax.set_yticks(range(-90, 91, 10), crs=projection)

        # Set the map extent if boundaries are provided
        if lat1 and lat2 and lon1 and lon2:
            ax.set_extent([lon1, lon2, lat1, lat2], crs=projection)

        # Add labels
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

        # Add coastlines and continents
        ax.add_feature(cfeature.LAND, color='lightgrey')

        # Add a legend for the reference track
        ax.legend()

        # Add title
        ax.set_title("Track Density (Var: {} - Seas: {} - ERA5)".format(var, seas))
        
        # Create the plot directory if it doesn't exist
        os.makedirs(plotdir, exist_ok=True)
        
        # Save plot
        plt.savefig(plotdir + f"vaia_trackdensity_ERA5.png")
        print("saved plot named: ", plotdir + f"vaia_trackdensity_ERA5.png")
        plt.close()
        
def read_filtered_tracks(ERA5_track_dir_vaia_analogue, filename):
    
    # example filename
    # concatenated_tracks_firstlatpass38_firstlonpass4_firstrad4_secondlatpass45_secondlonpass10_secondrad2_1940-2024.txt
    
    latpass1 = []
    lonpass1 = []
    rad1 = []
    latpass2 = []
    lonpass2 = []
    rad2 = []


    parts = filename.split('_')
    for part in parts:
        if part.startswith("firstlatpass"):
            latpass1.append(part.replace("firstlatpass", ""))
        elif part.startswith("firstlonpass"):
            lonpass1.append(part.replace("firstlonpass", ""))
        elif part.startswith("firstrad"):
            rad1.append(part.replace("firstrad", ""))
        elif part.startswith("secondlatpass"):
            latpass2.append(part.replace("secondlatpass", ""))
        elif part.startswith("secondlonpass"):
            lonpass2.append(part.replace("secondlonpass", ""))
        elif part.startswith("secondrad"):
            rad2.append(part.replace("secondrad", ""))
       
    #cast other values to floats
    latpass1 = float(latpass1[0])
    lonpass1 = float(lonpass1[0])
    rad1 = float(rad1[0])
    latpass2 = float(latpass2[0])
    lonpass2 = float(lonpass2[0])
    rad2 = float(rad2[0])

    print("filename: ", filename)
    print("latpass1: ", latpass1)
    print("lonpass1: ", lonpass1)
    print("rad1: ", rad1)
    print("latpass2: ", latpass2)
    print("lonpass2: ", lonpass2)
    print("rad2: ", rad2)
    
    return latpass1, lonpass1, rad1, latpass2, lonpass2, rad2
        

if __name__ == "__main__":
    
    plot_vaiagen_vaiapass = False
    plot_vaia_doublepass = False
    plot_all_tracks = False
    plot_florence = True
    
    
    if plot_vaiagen_vaiapass:
        vaia_track = read_ERA5_tracks(ERA5_track_dir_vaia, ERA5_track_vaia_filename)
        concatenated_tracks_filename, latgen, longen, radgen, latpas, lonpas, radpas = read_filtered_tracks(ERA5_track_dir_vaia_analogue)
        all_tracks = read_ERA5_tracks(ERA5_track_dir_vaia_analogue, concatenated_tracks_filename)
        plot_tracks(vaia_track, all_tracks, plotdir, lat1=30, lat2=65, lon1=-10, lon2=30, latgen=latgen, longen=longen, radgen=radgen, latpas=latpas, lonpas=lonpas, radpas=radpas)
    elif plot_all_tracks:
        all_tracks = read_ERA5_tracks
        plot_tracks(vaia_track, all_tracks, plotdir, lat1=30, lat2=65, lon1=-10, lon2=30)
    elif plot_vaia_doublepass:
        vaia_track = read_ERA5_tracks(ERA5_track_dir_vaia, ERA5_track_vaia_filename)
        concatenated_tracks_filename, latpass1, lonpass1, rad1, latpass2, lonpass2, rad2 = read_filtered_tracks(ERA5_track_dir_vaia_analogue, gen_pass=False)
        all_tracks = read_ERA5_tracks(ERA5_track_dir_vaia_analogue, concatenated_tracks_filename)
        plot_tracks(vaia_track, all_tracks, plotdir, lat1=30, lat2=65, lon1=-10, lon2=30, latgen=latpass1, longen=lonpass1, radgen=rad1, latpas=latpass2, lonpas=lonpass2, radpas=rad2, double_pass=True) 
    elif plot_florence:
        florence_track = read_ERA5_tracks(ERA5_track_dir_florence, ERA5_track_florence_filename)
        vaia_track = read_ERA5_tracks(ERA5_track_dir_vaia, ERA5_track_vaia_filename)
        # read the concatenated tracks from the filtered tracks
        latgen, longen, radgen, latpas, lonpas, radpas = read_filtered_tracks(ERA5_track_dir_vaia_analogue, concatenated_tracks_filename)
        all_tracks = read_ERA5_tracks(ERA5_track_dir_vaia_analogue, concatenated_tracks_filename)
        plot_florence_and_vaia(florence_track, vaia_track, all_tracks, plotdir, lat1=30, lat2=65, lon1=-10, lon2=30, latgen=latgen, longen=longen, radgen=radgen, latpas=latpas, lonpas=lonpas, radpas=radpas)