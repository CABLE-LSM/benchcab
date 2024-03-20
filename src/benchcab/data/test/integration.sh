#!/bin/bash

set -ex

CABLE_REPO="git@github.com:CABLE-LSM/CABLE.git"
CABLE_DIR=/scratch/$PROJECT/$USER/benchcab/CABLE

TEST_DIR=/scratch/$PROJECT/$USER/benchcab/integration
EXAMPLE_REPO="git@github.com:CABLE-LSM/bench_example.git"

# Remove CABLE and test work space, then recreate
rm -rf $CABLE_DIR
mkdir -p $CABLE_DIR

rm -rf $TEST_DIR
mkdir -p $TEST_DIR

# Clone local checkout for CABLE
git clone $CABLE_REPO $CABLE_DIR
cd $CABLE_DIR
# Note: This is temporary, to be removed once #258 is fixed
git reset --hard 67a52dc5721f0da78ee7d61798c0e8a804dcaaeb

# Clone the example repo
git clone $EXAMPLE_REPO $TEST_DIR
cd $TEST_DIR
git reset --hard 6287539e96fc8ef36dc578201fbf9847314147fb

cat > config.yaml << EOL
project: $PROJECT

realisations:
  - repo:
      local:
        path: $CABLE_DIR
  - repo:
      git:
        branch: main
        commit: 67a52dc5721f0da78ee7d61798c0e8a804dcaaeb  # Note: This is temporary, to be removed once #258 is fixed
modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]

fluxsite:
  experiment: AU-Tum
  pbs:
    storage:
      - scratch/$PROJECT
EOL

benchcab run -v