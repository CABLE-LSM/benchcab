#!/bin/bash
#PBS -l wd
#PBS -l ncpus=1
#PBS -l mem=8G
#PBS -l walltime=01:00:00
#PBS -q copyq
#PBS -P tm70
#PBS -j oe
#PBS -m e
#PBS -l storage=gdata/ks32+gdata/xp65+gdata/wd9+gdata/rp23

module purge

set -ev

# Set some things
DATA_DIR=runs/fluxsite/outputs
NUM_THREADS=1
CACHE_DELAY=300
MEORG_BIN=/opt/benchcab/bin/meorg
MODEL_PROFILE_ID=nFcjg4qqHGPkB9sqE
meorg_output_name=123-my-branch_A1B2C3
MODEL_OUTPUT_ARGS=()

# Create new model output entity
MODEL_OUTPUT_ARGS+="--state-selection default"
MODEL_OUTPUT_ARGS+=" --parameter-selection automated"

MODEL_OUTPUT_ARGS+=" --is-bundle"


# Create the model output, or get the ID of the existing one with this name.
# me.org refuses a name that belongs to another user.
MODEL_OUTPUT_ID="$($MEORG_BIN output create $MODEL_PROFILE_ID $meorg_output_name $MODEL_OUTPUT_ARGS | head -n 1 | awk '{print $NF}')"
[ -n "$MODEL_OUTPUT_ID" ]
echo "$meorg_output_name on me.org has this ID: $MODEL_OUTPUT_ID"

echo "Add experiments to model output"
$MEORG_BIN experiment update $MODEL_OUTPUT_ID jwN9jNMWLEzbT2i9D

 
echo "Add benchmarks to model output"
$MEORG_BIN benchmark update $MODEL_OUTPUT_ID jwN9jNMWLEzbT2i9D J9BBQCJdsuehsmMf2,N5X2rjmp96baXrrJ3,Q7Xu6yGGYdzvvAwbn

# Fetch the analysis inputs for the analysis job. The result job replaces the
# model output files after the analysis job, so if a job is stopped, the model
# output keeps the old files.
echo "$MODEL_OUTPUT_ID" > /work/runs/fluxsite/analysis/meorg/model_output_id
rm -f /work/runs/fluxsite/analysis/meorg/run.json /work/runs/fluxsite/analysis/meorg/output.json
$MEORG_BIN analysis input $MODEL_OUTPUT_ID jwN9jNMWLEzbT2i9D $DATA_DIR/*.nc --run-id benchcab-AU-Tum --cache /scratch/tm70/abc123/meorg-cache -o /work/runs/fluxsite/analysis/meorg/input.json

 
echo "Analysis inputs for $MODEL_OUTPUT_ID written to /work/runs/fluxsite/analysis/meorg/input.json"