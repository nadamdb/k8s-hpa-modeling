#!/bin/bash
for i in ../generator/measurement_2/*; do
	python3 measurement.py --wait-time 10 --config $i;
done
