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

# Clone the example repo
git clone $EXAMPLE_REPO $TEST_DIR
cd $TEST_DIR
git reset --hard 9bfba54ee8bf23141d95b1abe4b7207b0f3498e2

cat > config.yaml << EOL
project: $PROJECT

realisations:
  - repo:
      local:
        path: $CABLE_DIR
  meorg_output_name: true
  - repo:
      git:
        branch: main
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
      - gdata/$PROJECT
  # This ID is currently configured on the me.org server.
EOL

benchcab run -v
