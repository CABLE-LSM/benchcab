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

set -ev

MEORG_BIN=/opt/benchcab/bin/meorg
MODEL_OUTPUT_ID=$(cat /work/runs/fluxsite/analysis/meorg/model_output_id)

# Delete the files of an earlier run only now that the analysis job has
# finished. Delete them before the result, which waits for files with the same
# names and sizes as this run's.
echo "Deleting existing files from model output ID"
$MEORG_BIN file delete_all $MODEL_OUTPUT_ID

# Submit the result first, so that it does not wait for the upload
RESULT_STATUS=0
$MEORG_BIN analysis submit-result $MODEL_OUTPUT_ID jwN9jNMWLEzbT2i9D /work/runs/fluxsite/analysis/meorg --orchestrator benchcab || RESULT_STATUS=$?

# Upload the model output files with their original names. me.org matches them
# to the files recorded with the result by name and size.
echo "Uploading data to $MODEL_OUTPUT_ID"
$MEORG_BIN file upload runs/fluxsite/outputs/*.nc -n 1 $MODEL_OUTPUT_ID

exit $RESULT_STATUS