#!/bin/bash
#PBS -l wd
#PBS -l ncpus=18
#PBS -l mem=30GB
#PBS -l walltime=6:00:00
#PBS -q normal
#PBS -P tm70
#PBS -j oe
#PBS -m e
#PBS -l storage=gdata/ks32+gdata/hh5+gdata/wd9

set -ev

/absolute/path/to/benchcab fluxsite-run-tasks --config=/path/to/config.yaml