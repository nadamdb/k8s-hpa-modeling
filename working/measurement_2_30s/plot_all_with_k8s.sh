#!/usr/bin/env bash
rm -rf plots/
mkdir -p plots/
len=30
for i in {10,15,20,30};
    do for j in {1,2};
        do for seed in {0,1,2};
            do python3 ../../plotter/plotter.py --model-log \
            model_outputs/poisson_generated_times_length_${len}min_load_rate_${i}_serve_rate_${j}_random_seed_${seed}.discrete.out \
            --cont-model-log \
            model_outputs/poisson_generated_times_length_${len}min_load_rate_${i}_serve_rate_${j}_random_seed_${seed}.continuous.out \
            --k8s-log \
            k8s_measurement_length_${len}min_load_rate_${i}_serve_rate_${j}_random_seed_${seed}_timestamp* \
            --file-name plots/experiment_length-${len}min_load-rate-${i}_serve-rate-${j}_random_seed_${seed};
            done;
    done;
done
