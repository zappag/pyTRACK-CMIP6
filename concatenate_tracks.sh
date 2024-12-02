#!/bin/sh  

MODEL="EC-Earth3"
ENSM="*"
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
elif [ "$MODEL" = "ERA5" ]; then
    ff_files_path="/home/ghinassi/work/track_output/ERA5/${SEAS}/${VAR}"
    if [ "$VAR" = "msl" ]; then
        file_info="NH_ERA5_msl_6hr_*_${SEAS}"
    elif [ "$VAR" = "vor850" ]; then
        file_info="NH_ERA5_uv_6hr_*_${SEAS}_merged"
    fi
    total_tracks_path="/home/ghinassi/work/track_output/ERA5/SON/msl/total_tracks"
fi

echo "ff_files_path: $ff_files_path"

if [ "$MODEL" = "EC-Earth3" ]; then
    for ensm in $(ls -d /home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}/${ENSM}/); do
        ensm=$(basename "$ensm")
        total_tracks_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}/${ensm}/${VAR}/total_tracks"
        # Create the total_tracks_path if it doesn't exist
        mkdir -p "${total_tracks_path}"
        for ((year=Y1; year<=Y2; year++))
        do
            # Generate the file path for the current year
            if [ "$VAR" = "psl" ]; then
                year_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}/${ensm}/${VAR}/NH_${year}_T63mslp/dates/ff_trs_neg"
            elif [ "$VAR" = "vor850" ]; then
                year_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}/${ensm}/${VAR}/NH_${year}_uv/dates/ff_trs_pos"
            fi
            cat "$year_path" >> "$total_tracks_path/concatenated_tracks_${ensm}.txt"
        done
        echo "created file: $total_tracks_path/concatenated_tracks_${ensm}.txt"
    done
elif [ "$MODEL" = "ERA5" ]; then
    # Create the total_tracks_path if it doesn't exist
    mkdir -p "${total_tracks_path}"
    for year in $(seq $Y1 $Y2); do
        # Generate the file path for the current year
        if [ "$VAR" = "msl" ]; then
            year_path="/home/ghinassi/work/track_output/ERA5/$SEAS/${VAR}/NH_ERA5_msl_6hr_${year}_${SEAS}/dates/ff_trs_neg"
        elif [ "$VAR" = "vor850" ]; then
            year_path="/home/ghinassi/work/track_output/ERA5/$SEAS/${VAR}/NH_ERA5_uv_6hr_${year}_${SEAS}_merged/dates/ff_trs_pos.NAME"
        fi
        cat "$year_path" >> "$total_tracks_path/concatenated_tracks.txt"
    done
    echo "created file: $total_tracks_path/concatenated_tracks.txt"
fi                                 

