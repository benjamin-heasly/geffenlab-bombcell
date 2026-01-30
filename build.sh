#!/bin/sh

set -e

docker build -f environment/Dockerfile -t geffenlab/bombcell:local .

mkdir -p $PWD/results
docker run --rm \
  --volume /home/ninjaben/codin/geffen-lab-data/analysis/BH/AS20-minimal3/03112025/phy-export/AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0/tprime:/home/ninjaben/codin/geffen-lab-data/analysis/BH/AS20-minimal3/03112025/phy-export/AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0/tprime \
  --volume $PWD/results:$PWD/results \
  geffenlab/bombcell:local \
  conda_run python /opt/code/run.py \
  --phy-root /home/ninjaben/codin/geffen-lab-data/analysis/BH/AS20-minimal3/03112025/phy-export/AS20_03112025_trainingSingle6Tone2024_Snk3.1_g0/tprime \
  --bombcell-params-json '{"foo": "bar"}' \
  --results-dir $PWD/results
