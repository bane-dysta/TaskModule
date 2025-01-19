#!/bin/bash
#SBATCH -J sobMECI
#SBATCH --ntasks-per-node=64
#SBATCH -N 1
#SBATCH --mem=220000M
#SBATCH -p tyhctest

# 运行环境
source "$HOME/apprepo/orca/6.0.1-openmpi416_gcc930/scripts/env.sh"
source "$HOME/apprepo/gaussian/16-hy/scripts/env.sh"
export PGI_FASTMATH_CPU=sandybridge

# 运行sobMECP
./prepare.sh
./runfirst.sh
./runMECP.sh

