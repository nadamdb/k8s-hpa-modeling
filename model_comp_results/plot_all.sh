#!/usr/bin/env bash
rm -rf plots/
mkdir -p plots/
for i in 8 10 12 14 16 18;
    do for j in 1 2 3 4 5;
        do python3 ../plotter/plotter.py --model-log experiment_length-10min_load-rate-${i}_serve-rate-${j}.discrete.out \
        --cont-model-log experiment_length-10min_load-rate-${i}_serve-rate-${j}.continuous.out \
        --base-model-log experiment_length-10min_load-rate-${i}_serve-rate-${j}.baseline.out \
        --file-name plots/experiment_length-10min_load-rate-${i}_serve-rate-${j};
        done;
    done
