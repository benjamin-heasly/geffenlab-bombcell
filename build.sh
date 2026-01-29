#!/bin/sh

set -e

docker build -f environment/Dockerfile -t geffenlab/bombcell:local .

mkdir -p $PWD/results
docker run --rm \
  --volume /home/ninjaben/codin/geffen-lab-data/analysis/BH/AS20-minimal3/03112025:/home/ninjaben/codin/geffen-lab-data/analysis/BH/AS20-minimal3/03112025 \
  --volume $PWD/results:$PWD/results \
  geffenlab/bombcell:local \
  conda_run python /opt/code/run.py \
  --analysis-dir /home/ninjaben/codin/geffen-lab-data/analysis/BH/AS20-minimal3/03112025 \
  --results-dir $PWD/results \
