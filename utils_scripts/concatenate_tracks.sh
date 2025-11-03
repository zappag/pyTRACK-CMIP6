#!/bin/sh  

MODEL="EC-Earth3" # "EC-Earth3" or "ERA5"
ENSM="r18i1p1f1"  # or "all" for all ensemble members
SCEN="scenarioMIP"  # or "historical"
SCEN_NAME="ssp245"  # set to "None" if SCEN is historical
VAR="psl"
SEAS="SON"
Y1=2070
Y2=2100

# Set file_info for pattern matching
if [ "$VAR" = "psl" ]; then
    file_info="NH_*_T63mslp"
elif [ "$VAR" = "vor850" ]; then
    file_info="NH_*_uv_"
fi

# Set paths for EC-Earth3
if [ "$MODEL" = "EC-Earth3" ]; then
    if [ "$SCEN" = "scenarioMIP" ]; then
        ff_files_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SCEN_NAME}/${SEAS}/${ENSM}/${VAR}"
    else
        ff_files_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}/${ENSM}/${VAR}"
    fi

# Set paths for ERA5
elif [ "$MODEL" = "ERA5" ]; then
    ff_files_path="/home/ghinassi/work/track_output/ERA5/${SEAS}/${VAR}"
    if [ "$VAR" = "msl" ]; then
        file_info="NH_ERA5_msl_6hr_*_${SEAS}"
    elif [ "$VAR" = "vor850" ]; then
        file_info="NH_ERA5_uv_6hr_*_${SEAS}_merged"
    fi
    total_tracks_path="/home/ghinassi/work/track_output/ERA5/${SEAS}/${VAR}/total_tracks"
fi

echo "ff_files_path: $ff_files_path"

# EC-Earth3 loop
if [ "$MODEL" = "EC-Earth3" ]; then
    if [ "$SCEN" = "scenarioMIP" ]; then
        BASE_PATH="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SCEN_NAME}/${SEAS}"
    else
        BASE_PATH="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}"
    fi

    for ensm in $(ls -d ${BASE_PATH}/${ENSM}/); do
        ensm=$(basename "$ensm")
        total_tracks_path="${BASE_PATH}/${ensm}/${VAR}/total_tracks"
        mkdir -p "${total_tracks_path}"
        for year in $(seq $Y1 $Y2); do
            if [ "$VAR" = "psl" ]; then
                year_path="${BASE_PATH}/${ensm}/${VAR}/NH_${year}_T63mslp/dates/ff_trs_neg"
            elif [ "$VAR" = "vor850" ]; then
                year_path="${BASE_PATH}/${ensm}/${VAR}/NH_${year}_uv/dates/ff_trs_pos"
            fi
            cat "$year_path" >> "$total_tracks_path/concatenated_tracks_${ensm}.txt"
        done
        echo "created file: $total_tracks_path/concatenated_tracks_${ensm}.txt"
    done

# ERA5 loop
elif [ "$MODEL" = "ERA5" ]; then
    mkdir -p "${total_tracks_path}"
    for year in $(seq $Y1 $Y2); do
        if [ "$VAR" = "msl" ]; then
            year_path="/home/ghinassi/work/track_output/ERA5/$SEAS/${VAR}/NH_ERA5_msl_6hr_${year}_${SEAS}/dates/ff_trs_neg"
        elif [ "$VAR" = "vor850" ]; then
            year_path="/home/ghinassi/work/track_output/ERA5/$SEAS/${VAR}/NH_ERA5_uv_6hr_${year}_${SEAS}_merged/dates/ff_trs_pos"
        fi
        cat "$year_path" >> "$total_tracks_path/concatenated_tracks_ERA5.txt"
    done
    echo "created file: $total_tracks_path/concatenated_tracks_ERA5.txt"
fi
