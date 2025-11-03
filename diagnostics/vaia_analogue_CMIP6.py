import os
import matplotlib.pyplot as plt
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.stats import gaussian_kde

# this code reads the filtered tracks after the execution of the script pass_trajectories.sh.
# The tracks are then plotted on a map.

var="psl"
seas="SON"
model="EC-Earth3"
ensm="r4i1p1f1"

# dir with the vaia track to use as reference

ERA5_track_dir_vaia = f"/home/ghinassi/work/track_output/ERA5/SON/msl/NH_ERA5_msl_6hr_2018_SON/dates/"
ERA5_track_vaia_filename = "ff_trs_neg.vaiagen_vaiapass"
# other vaia analogous tracks to plot
CMIP6_track_dir_vaia_analogue = f"/home/ghinassi/work/track_output/CMIP6/{model}/historical/{seas}/{ensm}/{var}/vaia_analogue"

plotdir= "/home/ghinassi/work/diagnostics/plots/vaia_analogue/"

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


def plot_tracks(track_ref, alltracks, plotdir, lat1=None, lat2=None, lon1=None, lon2=None, latgen=None, longen=None, radgen=None, latpas=None, lonpas=None, radpas=None):
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
                linewidth=1.5,
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
                        linewidth=1,
                        color=color,
                        transform=projection)
                
        # Add latitude and longitude ticks
        ax.set_xticks(range(-180, 181, 30), crs=projection)
        ax.set_yticks(range(-90, 91, 10), crs=projection)

        # add genesis circle and passage circles as polygons
        if latgen and longen and radgen:
            print("adding genesis circle at lat: {}, lon: {}, rad: {}".format(latgen, longen, radgen))
            circle = plt.Circle((longen, latgen), radgen+1, color='red', fill=False, transform=ccrs.PlateCarree(), label="Genesis")
            ax.add_patch(circle)
        if latpas and lonpas and radpas:
            print("adding passage circle at lat: {}, lon: {}, rad: {}".format(latpas, lonpas, radpas))
            circle = plt.Circle((lonpas, latpas), radpas+1, color='blue', fill=False, transform=ccrs.PlateCarree(), label="Pass")
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


        ax.set_title("Ref: Vaia (Var: {} - Seas: {} - Model: {} - ensm: {}".format(var, seas, model, ensm))
        
        # Create the plot directory if it doesn't exist
        os.makedirs(plotdir, exist_ok=True)
        
        # Save plot
        plt.savefig(plotdir + f"alltracks_vaiaanalogue_{var}_{seas}_{model}_{ensm}_latgen{latgen}_longen{longen}_radgen{radgen}_latpas{latpas}_lonpas{lonpas}_radpas{radpas}.png")
        print("saved plot named: ", plotdir + f"alltracks_vaiaanalogue_{var}_{seas}_{model}_{ensm}_latgen{latgen}_longen{longen}_radgen{radgen}_latpas{latpas}_lonpas{lonpas}_radpas{radpas}.png")

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
        ax.set_title("Ref: Vaia (Var: {} - Seas: {} - Model: {} - ensm: {}".format(var, seas, model, ensm))
        
        # Create the plot directory if it doesn't exist
        os.makedirs(plotdir, exist_ok=True)
        
        # Save plot
        plt.savefig(plotdir + f"vaia_trackdensity_{var}_{seas}_{model}_{ensm}_latgen{latgen}_longen{longen}_radgen{radgen}_latpas{latpas}_lonpas{lonpas}_radpas{radpas}.png")
        print("saved plot named: ", plotdir + f"vaia_trackdensity_{var}_{seas}_{model}_{ensm}_latgen{latgen}_longen{longen}_radgen{radgen}_latpas{latpas}_lonpas{lonpas}_radpas{radpas}.png")
        plt.close()
        
def read_filtered_tracks(track_dir_vaia_analogue):
    # reads the filtered tracks after the execution of the script pass_trajectories.sh
    # then returns the complete filename and the lat, long and rad values for the generation and passage tracks
    # example of filename is:
    # concatenated_tracks_latgen38_longen4_radgen5_latpas48_lonpas5_radpas5.txt

    filename = []
    latgen = []
    longen = []
    radgen = []
    latpas = []
    lonpas = []
    radpas = []

    for file in os.listdir(track_dir_vaia_analogue):
        if file.startswith("concatenated_tracks_latgen"):
            filename.append(file)
            parts = file.split('_')
            for part in parts:
                if part.startswith("latgen"):
                    latgen.append(float(part.replace("latgen", "").replace(".txt", "")))
                elif part.startswith("longen"):
                    longen.append(float(part.replace("longen", "").replace(".txt", "")))
                elif part.startswith("radgen"):
                    radgen.append(float(part.replace("radgen", "").replace(".txt", "")))
                elif part.startswith("latpas"):
                    latpas.append(float(part.replace("latpas", "").replace(".txt", "")))
                elif part.startswith("lonpas"):
                    lonpas.append(float(part.replace("lonpas", "").replace(".txt", "")))
                elif part.startswith("radpas"):
                    radpas.append(float(part.replace("radpas", "").replace(".txt", "")))
        else:
            print("No file found")
            continue
    # cast filename as string
    filename = str(filename[0])
    #cast other values to floats
    latgen = float(latgen[0])
    longen = float(longen[0])
    radgen = float(radgen[0])
    latpas = float(latpas[0])
    lonpas = float(lonpas[0])
    radpas = float(radpas[0])


    print("filename: ", filename)
    print("latgen: ", latgen)
    print("longen: ", longen)
    print("radgen: ", radgen)
    print("latpas: ", latpas)
    print("lonpas: ", lonpas)
    print("radpas: ", radpas)
    
    return filename, latgen, longen, radgen, latpas, lonpas, radpas

    

vaia_track = read_ERA5_tracks(ERA5_track_dir_vaia, ERA5_track_vaia_filename)
concatenated_tracks_filename, latgen, longen, radgen, latpas, lonpas, radpas = read_filtered_tracks(CMIP6_track_dir_vaia_analogue)

all_tracks=read_ERA5_tracks(CMIP6_track_dir_vaia_analogue,concatenated_tracks_filename)

# plotting

track_density_plot=False

if track_density_plot:
    plot_track_density(vaia_track, all_tracks, plotdir, lat1=30, lat2=65, lon1=-10, lon2=30)   
else:
    plot_tracks(vaia_track, all_tracks, plotdir, lat1=30, lat2=65, lon1=-10, lon2=30, latgen=latgen, longen=longen, radgen=radgen, latpas=latpas, lonpas=lonpas, radpas=radpas)
