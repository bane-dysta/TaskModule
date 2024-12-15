#!/bin/bash

# Add MRCC to PATH
export PATH=$PATH:$HOME/apprepo/mrcc-2022

# Define periodic table mapping
declare -A elements=(
    [1]="H"   [2]="He"  [3]="Li"  [4]="Be"  [5]="B"   [6]="C"   [7]="N"   [8]="O"   [9]="F"   [10]="Ne"
    [11]="Na" [12]="Mg" [13]="Al" [14]="Si" [15]="P"  [16]="S"  [17]="Cl" [18]="Ar" [19]="K"  [20]="Ca"
    [21]="Sc" [22]="Ti" [23]="V"  [24]="Cr" [25]="Mn" [26]="Fe" [27]="Co" [28]="Ni" [29]="Cu" [30]="Zn"
    [31]="Ga" [32]="Ge" [33]="As" [34]="Se" [35]="Br" [36]="Kr" [37]="Rb" [38]="Sr" [39]="Y"  [40]="Zr"
    [41]="Nb" [42]="Mo" [43]="Tc" [44]="Ru" [45]="Rh" [46]="Pd" [47]="Ag" [48]="Cd" [49]="In" [50]="Sn"
    [51]="Sb" [52]="Te" [53]="I"  [54]="Xe"
)

# Get log file
log_file=$(ls *.log 2>/dev/null | head -n 1)
if [ -z "$log_file" ]; then
    echo "Error: No .log file found in current directory"
    exit 1
fi

# Get base name of log file (without extension)
base_name=$(basename "$log_file" .log)
xyz_file="${base_name}-mrcc.xyz"

# Create output directory
output_dir="../RS-PBEP86-SCS-ADC2"
mkdir -p "$output_dir"

# Create temporary files
temp_file=$(mktemp)
temp_coord_file=$(mktemp)

# Extract charge and multiplicity
charge_multi=$(grep "Charge =" "$log_file" | tail -n 1)
charge=$(echo "$charge_multi" | awk '{print $3}')
multiplicity=$(echo "$charge_multi" | awk '{print $6}')

# Extract the last Standard orientation coordinates
awk '
/Standard orientation:/ {
    delete coords
    count = 0
    for(i=1; i<=4; i++) getline
    while(getline && !/-{10,}/) {
        count++
        coords[count] = $2 " " $4 " " $5 " " $6
    }
}
END {
    if (count > 0) {
        for(i=1; i<=count; i++) print coords[i]
    }
}' "$log_file" > "$temp_coord_file"

# If Standard orientation not found, try Input orientation
if [ ! -s "$temp_coord_file" ]; then
    awk '
    /Input orientation:/ {
        delete coords
        count = 0
        for(i=1; i<=4; i++) getline
        while(getline && !/-{10,}/) {
            count++
            coords[count] = $2 " " $4 " " $5 " " $6
        }
    }
    END {
        if (count > 0) {
            for(i=1; i<=count; i++) print coords[i]
        }
    }' "$log_file" > "$temp_coord_file"
fi

# Count number of atoms
num_atoms=$(wc -l < "$temp_coord_file")

# Create XYZ file
{
    # First line: number of atoms
    echo "$num_atoms"
    # Second line: charge and multiplicity as comment
    echo "$charge $multiplicity"
    
    # Process coordinates and convert atomic numbers to element symbols
    while read -r line; do
        atomic_num=$(echo "$line" | awk '{print $1}')
        x=$(echo "$line" | awk '{print $2}')
        y=$(echo "$line" | awk '{print $3}')
        z=$(echo "$line" | awk '{print $4}')
        element="${elements[$atomic_num]:-$atomic_num}"
        echo "$element $x $y $z"
    done < "$temp_coord_file"
} > "$xyz_file"

# Move XYZ file to output directory
mv "$xyz_file" "$output_dir/"

# Change to output directory
cd "$output_dir" || exit 1

# Run genmrcc.sh
$HOME/apprepo/mrcc-2022/genmrcc.sh -m 96GB -n 32 -p tddft -d RS-PBE-P86 -D "scs-adc(2)" -b def2-TZVP -S 4 -T 3 "$xyz_file"

# Change to calculation directory
calc_dir="${base_name}-mrcc_RS-PBE-P86_TD_scsadc2"
cd "$calc_dir" || exit 1

# Update charge and multiplicity in MINP file
sed -i "s/charge=.*/charge=$charge/" MINP
sed -i "s/mult=.*/mult=$multiplicity/" MINP

# Return to parent directory
cd ..

# Get available SLURM partitions
partitions=$(sinfo -h -o "%R" | head -n 1)

# Create SLURM submission script
cat > mrcc.slurm << EOF
#!/bin/bash
#SBATCH -J RS-PBE-P86
#SBATCH --ntasks-per-node=32
#SBATCH -N 1
#SBATCH --mem=110000M
#SBATCH -p $partitions

# Set environment
export PATH=\$PATH:\$HOME/apprepo/mrcc-2022

# Run MRCC
bash ${base_name}-mrcc_RS-PBE-P86_TD_scsadc2/runmrcc.sh
EOF

echo "Setup completed successfully"

# Clean up temporary files
rm -f "$temp_file" "$temp_coord_file"