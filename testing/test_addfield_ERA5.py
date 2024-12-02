import track_wrapper
import sys
import os
import fnmatch
from pathlib import Path
#import yaml
#import subprocess


trackVarDir="/work_big/users/zappa/era5_test_track/"
trackVar="mslp"

run_track=False
run_add=False
run_stats=False
run_stats_add=True


### testing of mslp era5 tracking
refoutDir="/work_big/users/zappa/era5_test_track"
file_psl="ERA5_msl_6hr_1950_360t.nc"
ff=f"{trackVarDir}/{file_psl}"

if run_add:
    pr_file="/home/zappa/work_big/era5_test_track/ERA5_pr_6h_jja_1950.nc"
    track_file="/work_big/users/zappa/era5_test_track/NH_ERA5_msl_6hr_1950_JJA/ff_trs_neg"
    track_wrapper.add_mean_field(pr_file,track_file,5.,"TP",scaling=1000,hourshift=-5)

if run_stats:
    # test stats
    dirname="/work_big/users/zappa/era5_test_track/msl_tracks"
    track_wrapper.stats(dirname,"ff_trs_neg","std",2017,2017)

if run_stats_add:
    # test stats
    dirname="/work_big/users/zappa/era5_test_track/JJA"
    track_wrapper.stats(dirname,"ff_trs_neg.TP5mean","add1",1950,1950)


