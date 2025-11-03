import track_wrapper
import os
from pathlib import Path
import logging
#import yaml
#import subprocess

track_var="psl"
track_var_add="TP"
track_var_name_dir="total_precipitation"
freq_add_var="6hT00"
seas="SON"
model="EC-Earth3"
expn="scenarioMIP"
scenario="ssp245"
ensn="r22i1p1f1"


if model== "ERA5":
    trackVarDir=f"/home/ghinassi/work_big/ERA5/{track_var}/{seas}/"
    output_dirname=f"/home/ghinassi/work_big/ERA5/{seas}/{track_var}/"   
elif model=="EC-Earth3" and expn=="historical":
    trackVarDir=f"/home/ghinassi/work/track_output/CMIP6/{model}/{expn}/{seas}/{ensn}/{scenario}/{track_var}/"
    output_dirname=f"/home/ghinassi/work/track_output/CMIP6/{model}/{expn}/{seas}/{ensn}/{scenario}/{track_var}/"
elif model=="EC-Earth3" and expn=="scenarioMIP":
    trackVarDir=f"/home/ghinassi/work/track_output/CMIP6/{model}/{expn}/{scenario}/{seas}/{ensn}/{track_var}/"
    output_dirname=f"/home/ghinassi/work/track_output/CMIP6/{model}/{expn}/{scenario}/{seas}/{ensn}/{track_var}/"
    
# other parameters to set
radius = 5.0 #circle radius to perform averaging around the track for added field
year1 = 2070
year2 = 2100
scale_factor = 1000.0 #scaling factor for the added field, in this case to convert m to mm in total precipitation
hourshift = -4 #hour shift to apply to the added field, in this case -4 to match cumulated precipitation in which
               # the 6h total precipitation is accumulated at the end of the 6h period but first timestep is 3:30 (comes from CDO averaging)


run_track=False
run_add=False
run_stats=True
run_stats_add=False

# Set up logging
logging.basicConfig(level=logging.INFO)

### testing of mslp era5 tracking
refoutDir=f"/home/ghinassi/work/track_output/ERA5/{seas}/{track_var}/"

if run_add:
    for year in range(year1, year2 + 1):
        add_var_path = f"/home/ghinassi/work_big/ERA5/{track_var_name_dir}/{track_var_name_dir}/{freq_add_var}/{seas}/"
        add_var_file = f"ERA5_{track_var_name_dir}_{freq_add_var}_{year}_{seas}.nc"
        track_file = f"/home/ghinassi/work/track_output/ERA5/{seas}/{track_var}/NH_ERA5_msl_6hr_{year}_{seas}/ff_trs_neg"
        logging.info("add var field file is: %s", os.path.join(add_var_path, add_var_file))
        logging.info("track file is: %s", track_file)
        track_wrapper.add_field(dirname, track_file, radius, track_var_add, meanfield=False, scaling=scale_factor, hourshift=hourshift, cmip6=False)

if run_stats:
    track_wrapper.stats(output_dirname,"ff_trs_neg","std",year1,year2)

if run_stats_add:
    # test stats
    dirname="/work_big/users/zappa/era5_test_track/JJA"
    track_wrapper.stats(dirname,"ff_trs_neg.TP5mean","add1",1950,1950)
