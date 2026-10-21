#!/bin/bash
#PBS -l wd
#PBS -l ncpus=4
#PBS -l mem=16GB
#PBS -l walltime=00:30:00
#PBS -q normal
#PBS -P tm70
#PBS -j oe
#PBS -m e
#PBS -l storage=gdata/vk83

set -ev

module purge
module use /g/data/vk83/modules
module load r-meorg/1.0.7_0
export MEORG_MODULE=r-meorg/1.0.7_0 MEORG_RUN_ID=benchcab-AU-Tum

# meorg-run writes run.json for a failed analysis too, then exits 1.
# Carry on, so that the result job submits the failure to me.org.
meorg-run --input /work/runs/fluxsite/analysis/meorg/input.json --run-dir /work/runs/fluxsite/analysis/meorg || echo "meorg-run failed, see /work/runs/fluxsite/analysis/meorg/run.json"