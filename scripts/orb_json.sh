#!/bin/bash

# 1. Copy orb-viewer-config.json from script directory
# Get script directory and move up one level
script_dir="$(dirname "${BASH_SOURCE[0]}")/.."

# Copy config file from wfntxts directory
cp "${script_dir}/wfntxts/orb-viewer-config.json" .

# 2. Get basename of .log file in current directory
for logfile in *.log; do
    if [ -f "$logfile" ]; then
        # Get basename without extension
        basename=${logfile%.log}
        
        # 3. Create directory if it doesn't exist and move files
        target_dir="../Hole/${basename}"
        mkdir -p "$target_dir"
        
        # Move all .cub, .txt and .json files
        mv *.cub *.txt *.json "$target_dir" 2>/dev/null || true
        
        echo "Files moved to ${target_dir}"
    fi
done