#!/bin/bash
for load in {8,10,20,30}; do
	for serve in {1,2,4,8}; do
		for seed in {0,1,2}; do
			python3 timegenerator.py --length 60 --load-rate $load --serve-rate $serve --random-seed $seed;
		done; 
	done; 
done
