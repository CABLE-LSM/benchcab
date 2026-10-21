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

# Re-run analysis on the same model output ID, cleaning up existing files
echo "Deleting existing files from model output ID"
$MEORG_BIN file delete_all $MODEL_OUTPUT_ID

# Upload the data
echo "Uploading data to $MODEL_OUTPUT_ID"
$MEORG_BIN file upload $DATA_DIR/*.nc -n $NUM_THREADS $MODEL_OUTPUT_ID

# Wait for the cache to transfer to the object store.
echo "Waiting for object store transfer ($CACHE_DELAY sec)"
sleep $CACHE_DELAY

 
echo "Add benchmarks to model output"
$MEORG_BIN benchmark update $MODEL_OUTPUT_ID jwN9jNMWLEzbT2i9D J9BBQCJdsuehsmMf2,N5X2rjmp96baXrrJ3,Q7Xu6yGGYdzvvAwbn

# Trigger the analysis
echo "Triggering analysis on $MODEL_OUTPUT_ID"
$MEORG_BIN analysis start $MODEL_OUTPUT_ID jwN9jNMWLEzbT2i9D

 

MEORG_BASE_URL_DEV="${MEORG_BASE_URL_DEV:-https://modelevaluation.org/api/}"
echo "Files transferred to me.org. Analysis in progress. Open ${MEORG_BASE_URL_DEV}/display/${MODEL_OUTPUT_ID} to see results"