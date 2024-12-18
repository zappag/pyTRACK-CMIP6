#!/bin/sh  

MODEL="EC-Earth3"
ENSM="r2i1p1f1"
SCEN="historical"
VAR="psl"
SEAS="SON"
Y1=1940
Y2=2014

if [ "$MODEL" = "EC-Earth3" ]; then
    ff_files_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}/${ENSM}/${VAR}"
    if [ "$VAR" = "psl" ]; then
        file_info="NH_*_T63mslp"
    elif [ "$VAR" = "vor850" ]; then
        file_info="NH_*_uv_"
    fi
    vaia_analogue_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}/${ENSM}/${VAR}/vaia_analogue"
elif [ "$MODEL" = "ERA5" ]; then
    ff_files_path="/home/ghinassi/work/track_output/ERA5/${SEAS}/${VAR}"
    if [ "$VAR" = "msl" ]; then
        file_info="NH_ERA5_msl_6hr_*_${SEAS}"
    elif [ "$VAR" = "vor850" ]; then
        file_info="NH_ERA5_uv_6hr_*_${SEAS}_merged"
    fi
    vaia_analogue_path="/home/ghinassi/work/track_output/ERA5/SON/msl/vaia_analogue"
fi

echo "ff_files_path: $ff_files_path"

# /home/ghinassi/work/track_output/ERA5/$SON/vor850/NH_ERA5_uv_6hr_1940_SON_merged/dates/ff_trs_pos
# define the genesis and passing points

lat_gen=38
lon_gen=4
rad_gen=4

lat_pas=45
lon_pas=8
rad_pas=2

# define the count executable
count1=$HOME/track-master/utils/bin/count

echo "finding analogous trajectories to Vaia with: ${VAR}"

# Loop through the years
for year in $(seq $Y1 $Y2); do

    # Generate the file path for the current year
    if [ "$VAR" = "msl" ] || [ "$VAR" = "psl" ]; then
        ff="${ff_files_path}/$(echo $file_info/dates/ff_trs_neg | sed "s/\*/${year}/")"
    elif [ "$VAR" = "vor850" ]; then
        ff="${ff_files_path}/$(echo $file_info/dates/ff_trs_pos | sed "s/\*/${year}/")"
    fi

    # cleaning up direcories from vaia_analogue files

    if clean_dir=1; then
        rm -f ${ff}.vaiagen*
    fi

    echo "processing file: $ff for year: $year"

    ### filter genesis                                                                                                                             
    $count1 $ff $lat_gen $lon_gen $rad_gen 0 0

    # rename .new file in _vaiagen then add the coordinates                                                                       
    mv ${ff}.new ${ff}.vaiagen_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}

    ### filter passing                                                                        
    $count1 ${ff}.vaiagen_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen} $lat_pas $lon_pas $rad_pas 2 0

    # rename .new file in _vaiagen, e.g.                                                
    mv ${ff}.vaiagen_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}.new ${ff}.vaiagen_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}_vaiapass_latpas${lat_pas}_lonpas${lon_pas}_radpas${rad_pas}

done

# then concatenate tracks


# Create the vaia_analogue_path if it doesn't exist
mkdir -p "${vaia_analogue_path}"

if [ "$MODEL" = "EC-Earth3" ]; then
    for ((year=Y1; year<=Y2; year++))
    do
        # Generate the file path for the current year
        if [ "$VAR" = "psl" ]; then
            year_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}/${ENSM}/${VAR}/NH_${year}_T63mslp/dates/ff_trs_neg.vaiagen_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}_vaiapass_latpas${lat_pas}_lonpas${lon_pas}_radpas${rad_pas}"
        elif [ "$VAR" = "vor850" ]; then
            year_path="/home/ghinassi/work/track_output/ERA5/$SEAS/vor850/NH_ERA5_uv_6hr_${year}_${SEAS}_merged/dates/ff_trs_posNAME"
        fi
        cat "$year_path" >> "$vaia_analogue_path/concatenated_tracks_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}_latpas${lat_pas}_lonpas${lon_pas}_radpas${rad_pas}.txt"
    done
elif [ "$MODEL" = "ERA5" ]; then
    for year in $(seq $Y1 $Y2); do
        # Generate the file path for the current year
        if [ "$VAR" = "msl" ]; then
            year_path_gen="/home/ghinassi/work/track_output/ERA5/$SEAS/${VAR}/NH_ERA5_msl_6hr_${year}_${SEAS}/dates/ff_trs_neg.vaiagen_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}"
            year_path_gen_pass="/home/ghinassi/work/track_output/ERA5/$SEAS/${VAR}/NH_ERA5_msl_6hr_${year}_${SEAS}/dates/ff_trs_neg.vaiagen_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}_vaiapass_latpas${lat_pas}_lonpas${lon_pas}_radpas${rad_pas}"
        elif [ "$VAR" = "vor850" ]; then
            year_path="/home/ghinassi/work/track_output/ERA5/$SEAS/${VAR}/NH_ERA5_uv_6hr_${year}_${SEAS}_merged/dates/ff_trs_pos.NAME"
        fi
        cat "$year_path_gen" >> "$vaia_analogue_path/concatenated_tracks_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}.txt"
        cat "$year_path_gen_pass" >> "$vaia_analogue_path/concatenated_tracks_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}_latpas${lat_pas}_lonpas${lon_pas}_radpas${rad_pas}.txt"
    
    done
    echo "created file: $vaia_analogue_path/concatenated_tracks_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}.txt"
    echo "created file: $vaia_analogue_path/concatenated_tracks_latgen${lat_gen}_longen${lon_gen}_radgen${rad_gen}_latpas${lat_pas}_lonpas${lon_pas}_radpas${rad_pas}.txt"
fi                                  