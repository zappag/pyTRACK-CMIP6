#!/bin/bash

MODEL="ERA5"
SCEN="scenarioMIP"  # Historical or scenarioMIP
SCEN_NAME="ssp245"  # Scenario name for scenarioMIP
VAR="msl"  # MSL for ERA5, PSL for EC-Earth3
SEAS="SON"
Y1=1940
Y2=2024
ENSM="r18i1p1f1"  # "all" for all ensemble members or specific ensemble member

# Define the parameters for the two passes
# These parameters are used to filter the trajectories based on latitude, longitude, and radiusy

lat_pass1=38
lon_pass1=4
rad_pass1=4

lat_pass2=45
lon_pass2=10
rad_pass2=2

count1="$HOME/track-master/utils/bin/count"

# Get list of ensemble members
if [ "$MODEL" = "EC-Earth3" ]; then
    if [ "$SCEN" = "scenarioMIP" ]; then
        base_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SCEN_NAME}/${SEAS}"
    else
        base_path="/home/ghinassi/work/track_output/CMIP6/${MODEL}/${SCEN}/${SEAS}"
    fi
    if [ "$ENSM" = "all" ]; then
        ensm_list=($(find "$base_path" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;))
    else
        ensm_list=("$ENSM")
    fi
elif [ "$MODEL" = "ERA5" ]; then
    base_path="/home/ghinassi/work/track_output/ERA5/${SEAS}/${VAR}"
    ensm_list=("ERA5")  # Only one ensemble for ERA5
fi

echo "Processing model: $MODEL"
echo "Ensemble(s): ${ensm_list[*]}"

for ENSM in "${ensm_list[@]}"; do

    if [ "$MODEL" = "EC-Earth3" ]; then
        ff_files_path="${base_path}/${ENSM}/${VAR}"
        vaia_analogue_path="${ff_files_path}/vaia_analogue"
    elif [ "$MODEL" = "ERA5" ]; then
        ff_files_path="${base_path}"
        vaia_analogue_path="${ff_files_path}/vaia_analogue"
    fi

    mkdir -p "${vaia_analogue_path}"

    for year in $(seq $Y1 $Y2); do

        if [ "$MODEL" = "EC-Earth3" ]; then
            if [ "$VAR" = "psl" ]; then
                file_info="NH_${year}_T63mslp"
                ff="${ff_files_path}/${file_info}/dates/ff_trs_neg"
                echo "Processing ENSM: $ENSM with variable $VAR"

            elif [ "$VAR" = "vor850" ]; then
                file_info="NH_${year}_uv_"
                ff="${ff_files_path}/${file_info}/dates/ff_trs_pos"
            fi
        elif [ "$MODEL" = "ERA5" ]; then
            if [ "$VAR" = "msl" ]; then
                file_info="NH_ERA5_msl_6hr_${year}_${SEAS}"
                ff="${ff_files_path}/${file_info}/dates/ff_trs_neg"
                echo "Processing variable $VAR for ERA5"
            elif [ "$VAR" = "vor850" ]; then
                file_info="NH_ERA5_uv_6hr_${year}_${SEAS}_merged"
                ff="${ff_files_path}/${file_info}/dates/ff_trs_pos"
            fi
        fi

        if [ ! -f "$ff" ]; then
            echo "File not found: $ff"
            continue
        fi

        rm -f "${ff}.vaiapass"*

        echo "Processing year $year, file $ff"

        # First pass
        $count1 "$ff" $lat_pass1 $lon_pass1 $rad_pass1 2 0
        out1="${ff}.vaiapass_lat${lat_pass1}_lon${lon_pass1}_rad${rad_pass1}"
        mv "${ff}.new" "$out1"

        # Second pass
        $count1 "$out1" $lat_pass2 $lon_pass2 $rad_pass2 2 0
        out2="${out1}_vaiapass_lat${lat_pass2}_lon${lon_pass2}_rad${rad_pass2}"
        mv "${out1}.new" "$out2"

        # Append to concatenated files
        cat "$out1" >> "${vaia_analogue_path}/concatenated_tracks_firstlatpass${lat_pass1}_firstlonpass${lon_pass1}_firstrad${rad_pass1}_${Y1}-${Y2}.txt"
        cat "$out2" >> "${vaia_analogue_path}/concatenated_tracks_firstlatpass${lat_pass1}_firstlonpass${lon_pass1}_firstrad${rad_pass1}_secondlatpass${lat_pass2}_secondlonpass${lon_pass2}_secondrad${rad_pass2}_${Y1}-${Y2}.txt"
    done

    if [ "$MODEL" = "EC-Earth3" ]; then
        echo "Finished ENSM: $ENSM"
    fi
    echo "created file: ${vaia_analogue_path}/concatenated_tracks_firstlatpass${lat_pass1}_firstlonpass${lon_pass1}_firstrad${rad_pass1}_secondlatpass${lat_pass2}_secondlonpass${lon_pass2}_secondrad${rad_pass2}_${Y1}-${Y2}.txt"
done

echo "All done!"

