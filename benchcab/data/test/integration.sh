#!/bin/bash

set -ex

TEST_DIR=/scratch/$PROJECT/$USER/benchcab/integration
EXAMPLE_REPO="git@github.com:CABLE-LSM/bench_example.git"

# Remove the test work space, then recreate
rm -rf $TEST_DIR
mkdir -p $TEST_DIR

# Clone the example repo
git clone $EXAMPLE_REPO $TEST_DIR
cd $TEST_DIR
git reset --hard 6287539e96fc8ef36dc578201fbf9847314147fb

cat > config.yaml << EOL
project: $PROJECT

experiment: AU-Tum

realisations:
  - path: trunk
  - path: branches/Users/sb8430/test-branch

modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]

fluxsite:
    pbs:
        storage:
            - scratch/$PROJECT
EOL

benchcab run -v