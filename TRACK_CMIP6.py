import track_wrapper
import sys
import os
from cdo import *
from pathlib import Path

# select the input variable for TRACK, available are psl of vor850 (computed from u&v)
# input files are netcdf files from CMIP6 models

trackVar="psl"
seas="SON"
model="EC-Earth3"
expm="historical"
ensm="r25i1p1f1"
level=85000 #(in Pa)

# select years
y1=1940
y2=2015


# general output directory
refoutDir=f"/home/ghinassi/work/track_output/CMIP6/"

if seas:
    suboutDir=model+"/"+expm+"/"+seas+"/"+ensm+"/"+trackVar+"/"
else:
    suboutDir=model+"/"+expm+"/"+ensm+"/"+trackVar+"/"

outDir=refoutDir+suboutDir
Path(outDir).mkdir(parents=True, exist_ok=True)

run_track=True

# set the directories for the input files

if trackVar == "vor850":
    trackVarDir_u="/home/ghinassi/work/output/CMIP6/historical/EC-Earth3/6hrPt/atmos/6hrPlevPt/r1i1p1f1/ua/"
    trackVarDir_v="/home/ghinassi/work/output/CMIP6/historical/EC-Earth3/6hrPt/atmos/6hrPlevPt/r1i1p1f1/va/"
    if seas:
        trackVarDir_u=trackVarDir_u + seas + "/"
        trackVarDir_v=trackVarDir_v + seas + "/"
elif trackVar == "psl":
    trackVarDir_msl="/home/ghinassi/work/output/CMIP6/historical/EC-Earth3/6hr/atmos/6hrPlevPt/" + ensm + "/psl/"
    if seas:
        trackVarDir_msl=trackVarDir_msl + seas + "/"
else:
    print("trackVar not recognized")
    sys.exit(1)


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
        lev (int): The pressure level in hPa (optional if the file has more than one vertical lev).

    Returns:
        list: A list of matching file paths.
    """
    matching_files = []

    
    for root, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            parts = filename[:-3].split('_')
            if filename.endswith(f"{seas}.nc"):
                expm1 = parts[3]
                ensm1 = parts[4]
                year1 = int(parts[6])
                seas1 = parts[7]
                # if length parts is 8 then the file 
                #print(parts)
            elif len(parts) > 8:
                    raise Exception("File name not recognized")

            if expm1 == expm and ensm1 == ensm and seas1 == seas and ystart <= year1 <= yend:
                file_path = os.path.join(root, filename)
                matching_files.append(file_path)

    matching_files.sort()
    return matching_files

def search_files_expm(directory, expm, ensm, ystart, yend):
    """
    Search for files in the given directory that match the specified experiment, ensemble, and year range.

    Args:
        directory (str): The directory to search in.
        expm (str): The experiment name.
        ensm (str): The ensemble name.
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
            year1=int(parts[6][:4])

            if expm1 == expm and ensm1 == ensm and ystart <= year1 <= yend:
                file_path = os.path.join(root, filename)
                matching_files.append(file_path)

    matching_files.sort()
    return matching_files

def select_level(file, level=85000):
    """
    Select the vertical level from a netcdf file with cdo.
    Args:
        file (str): The file name.
        level (int): The pressure level in hPa.
    """

    file_out = file[:-3] + "_lev" + str(level) + ".nc"
    
    if os.path.exists(file_out):
        print("File already exists: ", file_out)
        return file_out
    else:
        cdo = Cdo()
        print("Selecting level ", level, "Pa")
        cdo.sellevel(str(level), input=file, output=file_out)
    return file_out


if run_track:
    print("model, expm and ensm are: " , model, expm, ensm)
    print("output directory for TRACK is: ", outDir)
    
    #if outdir is not found create it
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    
    """
    #check if outdir is not empty exit the code for safety (move within loop)
    if os.listdir(outDir):
        print(os.listdir(outDir))
        raise Exception("Output directory is not empty. Please provide an empty directory.")
    """
    
    if trackVar == "psl":
        print("tracking psl with cmip6 data")
        if seas is not None:
            print("season is: ", seas)
            mfile=search_files_expm_seas(trackVarDir_msl,expm,ensm,seas,y1,y2)
            for ff in mfile:
                print("msl input file is: ", ff)
                track_wrapper.track_mslp(ff, outDir, NH=True, ysplit=False,cmip6=True)
        else:
            print("computing tracks for the whole year")
            mfile=search_files_expm(trackVarDir_msl,expm,ensm,y1,y2)
        for ff in mfile:
            print("msl input file is: ", ff)
            print("tracking mslp with ERA5 data")
            track_wrapper.track_mslp(ff, outDir, NH=True, ysplit=False)
    elif trackVar == "vor850":
        print("tracking vor850 from u&v with CMIP6 data")
        if seas is not None:
            print("season is: ", seas)
            mfile_u = search_files_expm_seas(trackVarDir_u,expm,ensm,seas,y1,y2)
            mfile_v = search_files_expm_seas(trackVarDir_v,expm,ensm,seas,y1,y2)
        else:
            print("computing tracks for the whole year")
            mfile_u = search_files_expm(trackVarDir_u,expm,ensm,y1,y2)
            mfile_v = search_files_expm(trackVarDir_v,expm,ensm,y1,y2)
        for ff_u, ff_v in zip(mfile_u, mfile_v):

            print("u file: ", ff_u)
            print("v file: ", ff_v)
            if level:
                print("selected level is: ", level, "Pa")
                ff_u=select_level(ff_u,level)
                ff_v=select_level(ff_v,level)
            track_wrapper.track_uv_vor850(ff_u, outDir, ff_v, NH=True, ysplit=False, cmip6=True)