import precip_in_warning_regions_GP as pwr
import os
from datetime import datetime
import time
import argparse

# Parse command-line arguments
#parser = argparse.ArgumentParser(description="Process precipitation data for a specific ensemble or all ensembles.")
#parser.add_argument('--ensm', type=str, required=True, help="Ensemble member (e.g., r1i1p1f1) or 'all' for all ensemble members")
#args = parser.parse_args()
#ensm = args.ensm

cwd = os.getcwd()

######### Configuration for the script
base_hist_dir = "/home/ghinassi/nas_zappa/CMIP/output/CMIP6/historical/EC-Earth3/day/atmos/day/"
base_ssp_dir = "/home/ghinassi/nas_zappa/CMIP/output/CMIP6/ssp245/EC-Earth3/day/atmos/day/"
shapefile = os.path.join("/home/zappa/ENCIRCLE/shapefiles/ZA_2017_ID_v4_geowgs84.shp")
outputdir = '/home/ghinassi/work/ENCIRCLE_precipitation/output_precipitation_warning_regions'
model = 'EC-Earth3'
exp = 'concatenated'  # Set to 'historical' or 'scenarioMIP' for SSP scenarios
scenario = 'ssp245'
ensm='all'  # Set to 'all' to process all ensemble members or specify a specific ensemble member (e.g., 'r1i1p1f1')

os.makedirs(outputdir, exist_ok=True)

ens_list = [
    "r2i1p1f1", "r7i1p1f1", "r10i1p1f1", "r12i1p1f1", "r14i1p1f1", 
    "r16i1p1f1", "r17i1p1f1", "r18i1p1f1", "r19i1p1f1", "r20i1p1f1", 
    "r21i1p1f1", "r22i1p1f1", "r23i1p1f1", "r24i1p1f1", "r25i1p1f1"
]

sy = '1950-01-01'
ly = '2099-12-31'
scalef = 86400
qthreshold = 0.99

sy_clim = datetime(1984, 1, 1, 0, 0, 0)
ly_clim = datetime(2014, 12, 31, 23, 0, 0)

def get_ensemble_members(base_dir):
    return sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

def get_precip_files(ensm):
    if exp == 'historical':
        precip_dir = os.path.join(base_hist_dir, ensm, "pr")
        precip_files = sorted([
        os.path.join(precip_dir, file)
        for file in os.listdir(precip_dir)
        if file.endswith('.nc')
    ])
    elif exp == 'scenarioMIP':
        precip_dir = os.path.join(base_ssp_dir, ensm, "pr")
        precip_files = sorted([
        os.path.join(precip_dir, file)
        for file in os.listdir(precip_dir)
        if file.endswith('.nc')
    ])
    elif exp == 'concatenated':
        precip_dir_hist = os.path.join(base_hist_dir, ensm, "pr")
        precip_dir_ssp = os.path.join(base_ssp_dir, ensm, "pr")
        
        precip_files_hist = sorted([os.path.join(precip_dir_hist, file) for file in os.listdir(precip_dir_hist) if file.endswith('.nc')])
        precip_files_ssp = sorted([os.path.join(precip_dir_ssp, file) for file in os.listdir(precip_dir_ssp) if file.endswith('.nc')])
        # concatenate the two lists
        precip_files = precip_files_hist + precip_files_ssp
    else:
        raise ValueError(f"Unsupported experiment type: {exp}")

    return precip_files


def process_ensemble(ensm):
    precip_files = get_precip_files(ensm)
    if exp == 'historical':
        extout = f"{model}_{exp}_{ensm}"
    elif exp=='scenarioMIP':
        extout = f"{model}_{exp}_{scenario}_{ensm}"
    elif exp == 'concatenated':
        extout = f"{model}_concatenated_hist+ssp245_{ensm}"
    time_start = time.time()
    precip_wrt = pwr.process_precip(precip_files, 'pr', 'lat', 'lon', shapefile, qthreshold, sy, ly, sy_clim, ly_clim, scalef)
    time_end = time.time()
    print(f"[{ensm}] Processing time: {time_end - time_start} seconds")
    qthreshold_str = str(int(qthreshold * 100))
    fileout = f"{outputdir}/{extout}_{sy.replace('-','')}_{ly.replace('-','')}_P{qthreshold_str}_direct_noaverage_italy_gridpoint.xlsx"
    print(fileout)
    precip_wrt.to_excel(fileout, index=True)


if ensm == "all":
    for member in ens_list:
        process_ensemble(member)
else:
    process_ensemble(ensm)

