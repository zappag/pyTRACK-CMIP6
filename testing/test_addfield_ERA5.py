import track_wrapper
import sys
import os
import fnmatch
from pathlib import Path
#import yaml
#import subprocess


run_track_vor=True
run_track_mslp=False
run_add=False
run_stats=False
run_stats_add=False

# ### testing of vorticity era5 tracking
if run_track_vor:
    trackVar="vor850"
    trackVarDir="/work_big/users/zappa/era5_test_track/"
    file_u="ERA5_u_6hr_1950_10t.nc"
    file_v="ERA5_v_6hr_1950_10t.nc"
    ff_u=f"{trackVarDir}/uv/{file_u}"
    ff_v=f"{trackVarDir}/uv/{file_v}"
    refoutDir="/work_big/users/zappa/era5_test_track"
    track_wrapper.track_uv_vor850(ff_u, refoutDir, ff_v, NH=True, ysplit=False, cmip6=False)

### testing of mslp era5 tracking
if run_track_mslp:
    refoutDir="/work_big/users/zappa/era5_test_track"
    file_psl="ERA5_msl_6hr_1950_360t.nc"
    ff=f"{trackVarDir}/{file_psl}"
    track_wrapper.track_mslp_new(ff, refoutDir, 'ERA5_latest' ,NH=True, cmip6=False)

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


