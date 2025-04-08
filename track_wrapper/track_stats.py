import os
from cdo import *
from netCDF4 import Dataset
from pathlib import Path
from math import ceil
import subprocess
import glob

cdo = Cdo()

__all__ = ['track_stats']

def track_stats(indir, outdir, season='JJA', adaptive_smooth=True, cyclone=True):

    if os.path.isdir(outdir)==False:
        os.system('mkdir '+outdir)

    path=indir
    filelist=glob.glob(path+'*')

    if season=='DJF':
        start=[121, 245, 369]
        end=[244, 368, 480]
        file_ext=['dec', 'jan', 'feb']
    elif season=='JJA':
        start=[125, 245, 369]
        end=[248, 368, 492]
        file_ext=['jun', 'jul', 'aug']

    os.chdir(str(Path.home()) + "/TRACK")

    for e in filelist[:]:

        if cyclone:
            if e[len(path):len(path)+2]=='NH':
                file=e+'/ff_trs_pos'
            elif e[len(path):len(path)+2]=='SH':
                file=e+'/ff_trs_neg'
            else:
                print("ERROR! - ASh")
        else:
            if e[len(path):len(path)+2]=='NH':
                file=e+'/ff_trs_neg'
            elif e[len(path):len(path)+2]=='SH':
                file=e+'/ff_trs_pos'
            else:
                print("ERROR! - ASh")
            
        for i in range(3):
            if adaptive_smooth:
                os.system("sed -e \"s+FR_ST+"+ str(start[i]) + "+;s+FR_END+" + str(end[i]) + "+;s+FILE_NAME+" + str(file) + "+\" STATS_template.in > STATS_mod.in")
            else:
                os.system("sed -e \"s+FR_ST+"+ str(start[i]) + "+;s+FR_END+" + str(end[i]) + "+;s+FILE_NAME+" + str(file) + "+\" STATS_template_unsmooth.in > STATS_mod.in")
            
            os.system("bin/track.linux < STATS_mod.in")

            stat_filename=(e[len(path):]+'_'+file_ext[i])+'.nc'
            
            os.system("mv outdat/stat_trs_scl.linux_1.nc" +  " " + outdir+"/"+stat_filename)