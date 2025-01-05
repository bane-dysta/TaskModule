#!/bin/bash

# 1. Copy orb-viewer-config.json from script directory
# Get script directory and move up one level
script_dir="$(dirname "${BASH_SOURCE[0]}")/.."

# Copy config file from wfntxts directory
cp "${script_dir}/wfntxts/orb-viewer-config.json" .

# 2. Extract frontier orbital energies and numbers if mw_Eorb_out.txt exists
if [ -f "mw_Eorb_out.txt" ]; then
    # Find the last two occupied orbitals (HOMO-1 and HOMO)
    # and first two unoccupied orbitals (LUMO and LUMO+1)
    occupied=($(grep "Occ: 2.000000" mw_Eorb_out.txt | tail -n 2 | awk '{print $2, $5}'))
    unoccupied=($(grep "Occ: 0.000000" mw_Eorb_out.txt | head -n 2 | awk '{print $2, $5}'))
    
    # Extract orbital numbers (removing the colon)
    homo_minus1_num="${occupied[0]%:}"
    homo_num="${occupied[2]%:}"
    lumo_num="${unoccupied[0]%:}"
    lumo_plus1_num="${unoccupied[2]%:}"
    
    # Extract energies
    homo_minus1="${occupied[1]}"
    homo="${occupied[3]}"
    lumo="${unoccupied[1]}"
    lumo_plus1="${unoccupied[3]}"
    
    # Update orb-viewer-config.json
    if [ -f "orb-viewer-config.json" ]; then
        # Replace energies
        sed -i "s/\[HOMO-1\]/$homo_minus1/g" orb-viewer-config.json
        sed -i "s/\[HOMO\]/$homo/g" orb-viewer-config.json
        sed -i "s/\[LUMO\]/$lumo/g" orb-viewer-config.json
        sed -i "s/\[LUMO+1\]/$lumo_plus1/g" orb-viewer-config.json
        
        # Replace orbital numbers
        sed -i "s/\[NUMHOMO-1\]/$homo_minus1_num/g" orb-viewer-config.json
        sed -i "s/\[NUMHOMO\]/$homo_num/g" orb-viewer-config.json
        sed -i "s/\[NUMLUMO\]/$lumo_num/g" orb-viewer-config.json
        sed -i "s/\[NUMLUMO+1\]/$lumo_plus1_num/g" orb-viewer-config.json
    fi
fi

# 3. Find and process the log file
log_file=$(ls *.log 2>/dev/null | head -n 1)
if [ -n "$log_file" ]; then
    # Extract the last excited states block using awk
    awk '
    /Excited State   1:/ {
        delete excited_states
        count = 0
        in_block = 1
    }
    in_block {
        count++
        excited_states[count] = $0
    }
    /SavETr:/ {
        in_block = 0
    }
    END {
        if (count > 0) {
            for(i=1; i<=count; i++) print excited_states[i]
        }
    }' "$log_file" > temp_excited.txt
    
    if [ -s temp_excited.txt ]; then
        # Function to extract all transitions for a state
        extract_transitions() {
            state_num=$1
            awk -v state="Excited State   $state_num:" '
            $0 ~ state {p=1; next}
            /^$/ || /Excited State/ {p=0}
            p && /->/ {
                # Handle format "113 ->114         0.70168"
                from_orbital = $1
                to_orbital = $2
                sub("->", "", to_orbital)  # Remove -> from the second field
                coefficient = $3
                
                orbit = from_orbital "->" to_orbital "(" coefficient ")"
                if (NR == 1) {
                    printf "%s", orbit
                } else {
                    printf "\\n%s", orbit
                }
            }' temp_excited.txt
        }

        # Extract data for each state
        s1_data=$(grep "Excited State   1:" temp_excited.txt)
        s2_data=$(grep "Excited State   2:" temp_excited.txt)
        s3_data=$(grep "Excited State   3:" temp_excited.txt)

        # Extract wavelengths
        s1_wavelength=$(echo "$s1_data" | awk '{print $7}')
        s2_wavelength=$(echo "$s2_data" | awk '{print $7}')
        s3_wavelength=$(echo "$s3_data" | awk '{print $7}')

        # Extract f values
        s1_f=$(echo "$s1_data" | awk '{print $9}' | sed 's/f=//')
        s2_f=$(echo "$s2_data" | awk '{print $9}' | sed 's/f=//')
        s3_f=$(echo "$s3_data" | awk '{print $9}' | sed 's/f=//')

        # Extract all transitions for each state
        s1_to=$(extract_transitions 1) 
        s2_to=$(extract_transitions 2)
        s3_to=$(extract_transitions 3)
        
        # Remove temporary file
        rm temp_excited.txt
        
        # Create a temporary file for the new JSON content
        while IFS= read -r line; do
            line="${line//\[wavelength_S1\]/$s1_wavelength}"
            line="${line//\[wavelength_S2\]/$s2_wavelength}"
            line="${line//\[wavelength_S3\]/$s3_wavelength}"
            line="${line//\[f1\]/$s1_f}"
            line="${line//\[f2\]/$s2_f}"
            line="${line//\[f3\]/$s3_f}"
            line="${line//\[TO1\]/$s1_to}"
            line="${line//\[TO2\]/$s2_to}"
            line="${line//\[TO3\]/$s3_to}"
            echo "$line"
        done < orb-viewer-config.json > temp_config.json

        # Replace the original file
        mv temp_config.json orb-viewer-config.json
    fi
fi

# 4. Get basename of .log file in current directory
for logfile in *.log; do
    if [ -f "$logfile" ]; then
        # Get basename without extension
        basename=${logfile%.log}
        
        # 5. Create directory if it doesn't exist and move files
        target_dir="../Hole/${basename}"
        mkdir -p "$target_dir"
        
        # Move all .cub, .txt and .json files
        mv *.cub *.txt *.json "$target_dir" 2>/dev/null || true
        
        echo "Files moved to ${target_dir}"
    fi
done