import track_wrapper
import os
from pathlib import Path
#import yaml
#import subprocess

track_var="msl"
track_var_add="TP"
track_var_name_dir="total_precipitation"
freq_add_var="6hT00"
seas="SON"
trackVarDir=f"/home/ghinassi/work_big/ERA5/{track_var}/{seas}/"

# other parameters to set
radius = 5.0 #circle radius to perform averaging around the track for added field
year1 = 1940
year2 = 2024
scale_factor = 1000.0 #scaling factor for the added field, in this case to convert m to mm in total precipitation
hourshift = -4 #hour shift to apply to the added field, in this case -4 to match cumulated precipitation in which
               # the 6h total precipitation is accumulated at the end of the 6h period but first timestep is 3:30 (comes from CDO averaging)


run_track=False
run_add=True
run_stats=False
run_stats_add=False


### testing of mslp era5 tracking
refoutDir=f"/home/ghinassi/work/track_output/ERA5/{seas}/{track_var}/"

if run_add:
    for year in range(year1, year2 + 1):
        add_var_path = f"/home/ghinassi/work_big/ERA5/{track_var_name_dir}/{track_var_name_dir}/{freq_add_var}/{seas}/"
        add_var_file = f"ERA5_{track_var_name_dir}_{freq_add_var}_{year}_{seas}.nc"
        track_file = f"/home/ghinassi/work/track_output/ERA5/{seas}/{track_var}/NH_ERA5_msl_6hr_{year}_{seas}/ff_trs_neg"
        track_wrapper.add_field(os.path.join(add_var_path, add_var_file), track_file, radius, track_var_add, meanfield=False, scaling=scale_factor, hourshift=hourshift, cmip6=False)

if run_stats:
    # test stats
    dirname="/work_big/users/zappa/era5_test_track/msl_tracks"
    track_wrapper.stats(dirname,"ff_trs_neg","std",2017,2017)

if run_stats_add:
    # test stats
    dirname="/work_big/users/zappa/era5_test_track/JJA"
    track_wrapper.stats(dirname,"ff_trs_neg.TP5mean","add1",1950,1950)


