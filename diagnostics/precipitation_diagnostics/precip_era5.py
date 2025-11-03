import precip_in_warning_regions_GP as pwr
import os
from datetime import datetime
import time
import argparse

## UNCOMMENT TO USE COMMAND LINE ARGUMENTS

# # Parse command-line arguments
# parser = argparse.ArgumentParser(description="Process precipitation data for a specific ensemble.")
# parser.add_argument('--ensm', type=str, required=True, help="Ensemble member (e.g., r1i1p1f1)")
# args = parser.parse_args()

# # Get the ensemble member from the command-line argument
# ensm = args.ensm

cwd=cwd = os.getcwd()

######### Configuration for the script
# precip files is the full list of files that need to be processed from a single experiment, ordered in time.
precip_dir = f"/work/users/clima/zappa/ERA5/store/total_precipitation/day/"
precip_files = sorted([os.path.join(precip_dir, file) for file in os.listdir(precip_dir) if '1950-2024' in file and file.endswith('.nc')])

shapefile=os.path.join("/home/zappa/ENCIRCLE/shapefiles/ZA_2017_ID_v4_geowgs84.shp")

# directory and extension of the output files
outputdir = '/home/ghinassi/precipitation_diagnostics/ERA5/'
extout = 'ERA5'
save_to_excel = False  # Set to True to save output as Excel, False for CSV
# Ensure the output directory exists
os.makedirs(outputdir, exist_ok=True)


sy='1950-01-01'   # period to anlayse in file 
ly='2024-12-31'
scalef=86400      # unit: kg/m2 -> mm/day
qthreshold=0.99   # threshold on precipitation intensity of wet days

# period used to define reference climatology to define extreme events
sy_clim = datetime(1979, 1, 1, 0, 0, 0)
ly_clim = datetime(2014, 12, 31, 23, 0, 0)

########### Running the function
# run the function to process the precipitation data
# and get the output in a pandas dataframe
time_start=time.time()
precip_wrt=pwr.process_precip(precip_files,'TP','lat','lon',shapefile,qthreshold,sy,ly,sy_clim,ly_clim,scalef)
time_end=time.time()
print(f"Processing time: {time_end - time_start} seconds")

########### save output to Excel (if needed)
qthreshold_str = str(int(qthreshold * 100))

if save_to_excel == True:
    fileout=f"{outputdir}/{extout}_{sy.replace('-','')}_{ly.replace('-','')}_P{qthreshold_str}_direct_noaverage_italy_gridpoint.xlsx"
    precip_wrt.to_excel(fileout, index=True)
    print("file saved to:", fileout)
else:
    fileout_txt = f"{outputdir}/{extout}_{sy.replace('-','')}_{ly.replace('-','')}_P{qthreshold_str}_direct_noaverage_italy_gridpoint.csv"
    precip_wrt.to_csv(fileout_txt, index=True)
    print("file saved to:", fileout_txt)

