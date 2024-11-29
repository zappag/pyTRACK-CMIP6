import track_wrapper
import sys
import os
import fnmatch
from pathlib import Path
#import yaml
#import subprocess

var='mslp'

if var == 'vor850':
    ### testing of vorticity 
    trackVarDir="/work_big/users/zappa/ec-earth_test_track/"
    trackVar="vor850"
    file_u="ec-earth_ua_1940_son.nc"
    file_v="ec-earth_va_1940_son.nc"
    refoutDir="/work_big/users/zappa/ec-earth_test_track"
    ff_u=f"{trackVarDir}/uv/{file_u}"
    ff_v=f"{trackVarDir}/uv/{file_v}"
    track_wrapper.track_uv_vor850(ff_u, refoutDir, ff_v, NH=True, netcdf=False, ysplit=False)
elif var == 'mslp': 
    ### testing of mslp
    trackVarDir="/work_big/users/zappa/ec-earth_test_track/"
    file_psl="psl_6hrPlev_EC-Earth3_historical_r1i1p1f1_gr_2007_SON.nc"
    outdirectory="/work_big/users/zappa/ec-earth_test_track"
    ff_psl=f"{trackVarDir}/{file_psl}"
    track_wrapper.track_mslp(ff_psl, outdirectory,  NH=True, ysplit=False)
    
