import track_wrapper
import sys
import os
import fnmatch
from pathlib import Path
#import yaml
#import subprocess

track_var="msl"
track_var_add="TP"
seas="SON"
trackVarDir=f"/home/ghinassi/work_big/ERA5/{track_var}/{seas}/"

# other parameters to set
radius = 5.0 #circle radius to perform averaging around the track for added field
year1 = 2018
year2 = 2018

run_track=False
run_add=True
run_stats=False
run_stats_add=False


### testing of mslp era5 tracking
refoutDir=f"/home/ghinassi/work/track_output/ERA5/{seas}/{track_var}/"

if run_add:
    for year in range(year1, year2 + 1):
        add_var_file = f"/home/ghinassi/work_big/ERA5/total_precipitation/{seas}/ERA5_total_precipitation_6hT00_{year}_{seas}.nc"
        track_file = f"/home/ghinassi/work/track_output/ERA5/{seas}/{track_var}/NH_ERA5_msl_6hr_{year}_{seas}/ff_trs_neg"
        track_wrapper.add_mean_field(add_var_file, track_file, radius, track_var_add, scaling=1000, hourshift=-5, cmip6=False)

if run_stats:
    # test stats
    dirname="/work_big/users/zappa/era5_test_track/msl_tracks"
    track_wrapper.stats(dirname,"ff_trs_neg","std",2017,2017)

if run_stats_add:
    # test stats
    dirname="/work_big/users/zappa/era5_test_track/JJA"
    track_wrapper.stats(dirname,"ff_trs_neg.TP5mean","add1",1950,1950)


