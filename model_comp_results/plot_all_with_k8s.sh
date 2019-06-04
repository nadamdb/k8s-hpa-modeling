#!/usr/bin/env bash
rm -rf plots/
mkdir -p plots/
len=30
for i in {4,10,20};
    do for j in {2,6,10};
        do python3 ../plotter/plotter.py --model-log experiment_length-${len}min_load-rate-${i}_serve-rate-${j}.discrete.out \
        --cont-model-log experiment_length-${len}min_load-rate-${i}_serve-rate-${j}.continuous.out \
        --k8s-log ../working/$1/k8s_measurement_length_${len}min_load_rate_${i}_serve_rate_${j}_random_seed_0_timestamp* \
        --file-name plots/experiment_length-${len}min_load-rate-${i}_serve-rate-${j};
        done;
    done

