#!/bin/bash

# Get all .log files in current directory
for logfile in *.log; do
    if [ -f "$logfile" ]; then
        # Get basename without extension
        basename=${logfile%.log}
        
        # Check if basename starts with "td"
        if [[ $basename == td* ]]; then
            # Create initial and final filenames
            initial_file="${basename}.fchk"
            final_file="opt${basename:2}.fchk"
            
            # Create Huang-Rhys.gjf in ../FCclasses directory
            mkdir -p ../FCclasses
            cd ../FCclasses
            
            cat > Huang-Rhys.gjf << EOF
%oldchk=${final_file}
#p geom=allcheck freq(readfc,fcht,readfcht)
initial=source=chk final=source=chk spectroscopy=onephotonemission
print=(huangrhys,matrix=JK)

${initial_file}
${final_file}
EOF
            
            echo "Created Huang-Rhys.gjf for ${logfile}"
            cd - > /dev/null
        fi
    fi
done