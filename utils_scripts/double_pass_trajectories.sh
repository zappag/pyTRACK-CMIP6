#!/bin/sh  

MODEL="ERA5"
ENSM="*"
SCEN="historical"
VAR="msl"
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
# define the 2 passing points

lat_pass1=38
lon_pass1=4
rad_pass1=4

lat_pass2=45
lon_pass2=8
rad_pass2=4

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

    # cleaning up directories from vaia_analogue files

    if clean_dir=1; then
        rm -f ${ff}.vaiapass*
    fi

    echo "processing file: $ff for year: $year"

    ### filter passing 1                                                                                                                             
    $count1 $ff $lat_pass1 $lon_pass1 $rad_pass1 0 0

    # rename .new file in _vaiapass1 then add the coordinates                                                                       
    mv ${ff}.new ${ff}.vaiapass_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}

    ### filter passing 2                                                                        
    $count1 ${ff}.vaiapass_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1} $lat_pass2 $lon_pass2 $rad_pass2 2 0

    # rename .new file in _vaiapass2, e.g.                                                
    mv ${ff}.vaiapass_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}.new ${ff}.vaiapass_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}_vaiapass_lat${lat_pass2}_lon${lon_pass2}_rad${rad_pass2}

done

# then concatenate tracks


# Create the vaia_analogue_path if it doesn't exist
mkdir -p "${vaia_analogue_path}"

if [ "$MODEL" = "EC-Earth3" ]; then
    for ((year=Y1; year<=Y2; year++))
    do
        # Generate the file path for the current year
        if [ "$VAR" = "psl" ]; then
            year_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}/${ENSM}/${VAR}/NH_${year}_T63mslp/dates/ff_trs_neg.vaiapass_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}_vaiapass_lat${lat_pass2}_lon${lon_pass2}_rad${rad_pass2}"
        elif [ "$VAR" = "vor850" ]; then
            year_path="/home/ghinassi/work/track_output/ERA5/$SEAS/vor850/NH_ERA5_uv_6hr_${year}_${SEAS}_merged/dates/ff_trs_posNAME"
        fi
        cat "$year_path" >> "$vaia_analogue_path/concatenated_tracks_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}_lat${lat_pass2}_lon${lon_pass2}_rad${rad_pass2}.txt"
    done
elif [ "$MODEL" = "ERA5" ]; then
    for year in $(seq $Y1 $Y2); do
        # Generate the file path for the current year
        if [ "$VAR" = "msl" ]; then
            year_path_pass1="/home/ghinassi/work/track_output/ERA5/$SEAS/${VAR}/NH_ERA5_msl_6hr_${year}_${SEAS}/dates/ff_trs_neg.vaiapass_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}"
            year_path_pass2="/home/ghinassi/work/track_output/ERA5/$SEAS/${VAR}/NH_ERA5_msl_6hr_${year}_${SEAS}/dates/ff_trs_neg.vaiapass_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}_vaiapass_lat${lat_pass2}_lon${lon_pass2}_rad${rad_pass2}"
        elif [ "$VAR" = "vor850" ]; then
            year_path="/home/ghinassi/work/track_output/ERA5/$SEAS/${VAR}/NH_ERA5_uv_6hr_${year}_${SEAS}_merged/dates/ff_trs_pos.NAME"
        fi
        cat "$year_path_pass1" >> "$vaia_analogue_path/concatenated_tracks_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}.txt"
        cat "$year_path_pass2" >> "$vaia_analogue_path/concatenated_tracks_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}_lat${lat_pass2}_lon${lon_pass2}_rad${rad_pass2}.txt"
    
    done
    echo "created file: $vaia_analogue_path/concatenated_tracks_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}.txt"
    echo "created file: $vaia_analogue_path/concatenated_tracks_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}_lat${lat_pass2}_lon${lon_pass2}_rad${rad_pass2}.txt"
fi                                  