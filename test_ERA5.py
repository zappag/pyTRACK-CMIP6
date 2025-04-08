import track_wrapper
import sys
import os
import fnmatch
from pathlib import Path
#import yaml
#import subprocess


#trackVarDir_msl="/home/ghinassi/work_big/ERA5/msl/"
trackVarDir_u="/home/ghinassi/work_big/ERA5/u/"
trackVarDir_v="/home/ghinassi/work_big/ERA5/v/"
trackVar="vor850"

ff_u=trackVarDir_u + "ERA5_u_test.nc"
ff_v=trackVarDir_v + "ERA5_v_test.nc"
#file_psl="ERA5_mslp_6hr_1950.grb"
#file_u="ua/ua_6hrPlevPt_EC-Earth3_historical_r1i1p1f1_gr_185001010000-185012311800.nc"
#file_v="va/va_6hrPlevPt_EC-Earth3_historical_r1i1p1f1_gr_185001010000-185012311800.nc"

def search_files_expm_seas(directory, expm, ensm, seas, ystart, yend):
    """
    Search for files in the given directory that match the specified experiment, ensemble, season, and year range.

    Args:
        directory (str): The directory to search in.
        expm (str): The experiment name.
        ensm (str): The ensemble name.
        seas (str): The season.
        ystart (int): The start year.
        yend (int): The end year.

    Returns:
        list: A list of matching file paths.
    """
    matching_files = []
    
    for root, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            parts = filename[:-3].split('_')
            expm1=parts[3]
            ensm1=parts[4]
            year1=int(parts[6])
            seas1=parts[7]

            if expm1 == expm and ensm1 == ensm and seas1 == seas and ystart <= year1 <= yend:
                file_path = os.path.join(root, filename)
                matching_files.append(file_path)

    matching_files.sort()
    return matching_files

def search_files_ERA5(directory, ystart, yend, trackvar=None):
    """
    Search for files in the given directory with ERA5 standard.
    example of ERA5 file name: ERA5_msl_6hr_1950.grb

    Args:
        directory (str): The directory to search in.
        ystart (int): The start year.
        yend (int): The end year.

    Returns:
        list: A list of matching file paths.
    """
    matching_files = []
    
    for root, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith("_merged.nc"):
                continue
            
            parts = filename[:-3].split('_')
            var = parts[1]
            time_res = parts[2]
            year = int(parts[3])
            
            if var == trackvar and ystart <= year <= yend:
                file_path = os.path.join(root, filename)
                print(file_path)
                matching_files.append(file_path)

    matching_files.sort()
    
    return matching_files

# general output directory
refoutDir="/home/ghinassi/work/track_output/ERA5/"
seas=None

if seas:
    suboutDir = seas + "/" + trackVar + "/"
else:
    suboutDir = trackVar + "/"

outDir = refoutDir + suboutDir
Path(outDir).mkdir(parents=True, exist_ok=True)

track_wrapper.track_era5_vor850(ff_u, outDir, ff_v, NH=True, netcdf=False, ysplit=True)

run_track=True

y1=1950
y2=1951

raise SystemExit

if run_track:
    print("output directory for TRACK is: ", outDir)
    
    #if outdir is not found create it
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    
    #check if outdir is not empty exit the code for safety
    if os.listdir(outDir):
        print(os.listdir(outDir))
        raise Exception("Output directory is not empty. Please provide an empty directory.")
    
    if trackVar == "msl":
        mfile=search_files_ERA5(trackVarDir_msl,y1,y2,trackVar)
        print (mfile)
        for ff in mfile:
            print(ff)
            print("tracking mslp on ERA5 data")
            track_wrapper.track_era5_mslp(ff, refoutDir, NH=True, netcdf=False)
    elif trackVar == "vor850":
        print("tracking vor850 from u&v")
        mfile_u = search_files_ERA5(trackVarDir_u,y1,y2, trackvar="u")
        mfile_v = search_files_ERA5(trackVarDir_v,y1,y2, trackvar="v")
        for ff_u, ff_v in zip(mfile_u, mfile_v):

            print("u file: ", ff_u)
            print("v file: ", ff_v)
            track_wrapper.track_era5_vor850(ff_u, outDir, ff_v, NH=True, netcdf=False, ysplit=True)



"""
### main
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# switch
run_track=config['run_track']
run_stats=config['run_stats']
run_ens_mean=config['run_ens_mean'] 
trackVar=config['trackVar']
experiments=config['expm']
ensembles=config['ensm']
seasons=config['seas']

# directory names
if trackVar == "psl":    
    trackVarDir='/ec/res4/scratch/ccvm/tipes/AMIPs/6hrPlevPt/psl_seas/'
elif trackVar == "vor":
    trackVarDir='/ec/res4/scratch/ccvm/tipes/AMIPs/6hrPlevPt/uv850_seas/'
    
for expm in experiments:

    # experiment name
    if expm == "piControl":
        ys=1851
        ye=1860
        expm_lab='piControl-amip'
    elif expm == "ho-mid":
        ys=1863
        ye=1872
        expm_lab= "ho03-amip"
    elif expm == "ho-end":
        ys=1980
        ye=1989
        expm_lab= "ho03-amip"
        
    for ensm in ensembles:
        for seas in seasons:
            
            # general output directory
            refoutDir='/ec/res4/scratch/ccgz/tipes/track/AMIP/'
            suboutDir=expm+"/"+seas+"/"+ensm+"/"+trackVar+"/"
            outDir=refoutDir+suboutDir
            Path(outDir).mkdir(parents=True, exist_ok=True)
                
            # loop over files and run tracking
            if run_track:
                #mfile=search_files_with_string_pattern(trackVarDir,"*"+expm_lab+"*"+ensm+"*"+seas+"*")
                mfile=search_files_expm(trackVarDir,expm_lab,ensm,seas,ys,ye)

                for ff in mfile:
                    print(ff)
                    track_wrapper.track_mslp(ff,outDir,True,True)
                    #track_wrapper.track_uv_vor850(datadir1+fileUV,outputdir)
                        

            # run statistics
            if run_stats:
                track_wrapper.track_stats(outDir,'ff_trs_neg','test')

    # Ensemble statistics
    if run_ens_mean:
        print(refoutDir)
        ensmdir=refoutDir + '/' + expm + '/' + seas + '/'    
        patt='*/r*'+'/'+trackVar +'/total/stat_trs_scl.test_1.nc'
        stat_files=search_files_with_string_pattern2(ensmdir,patt)

        Path(ensmdir+"/ensmean/"+trackVar).mkdir(parents=True, exist_ok=True)
        stat_file_mean=ensmdir+"/ensmean/"+trackVar+"/stat_trs_scl.test_1.nc"
        subprocess.run(["cdo","ensmean",' '.join(stat_files),stat_file_mean])
"""

