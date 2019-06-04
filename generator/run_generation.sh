#!/bin/bash
for load in {10,15,20,30}; do
	for serve in {1,2}; do
		for seed in {0,1,2}; do
			python3 timegenerator.py --length 30 --load-rate $load --serve-rate $serve --random-seed $seed; 
		done; 
	done; 
done
