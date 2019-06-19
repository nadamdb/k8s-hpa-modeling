#!/bin/bash
for serve in {1,2}; do
    for seed in {0,1,2}; do
        python3 timegenerator.py --type mmpp --length 90 --load-rate-list $(($serve*10)) $(($serve*7)) --trans-matrix 0.5 0.5 0.5 0.5 --serve-rate $serve --random-seed $seed;
        python3 timegenerator.py --type mmpp --length 90 --load-rate-list $(($serve*15)) $(($serve*5)) --trans-matrix 0.75 0.25 0.75 0.25 --serve-rate $serve --random-seed $seed;
        python3 timegenerator.py --type mmpp --length 90 --load-rate-list $(($serve*20)) $(($serve*2)) --trans-matrix 0.25 0.75 0.25 0.75 --serve-rate $serve --random-seed $seed;
    done;
done