#!/bin/bash
for i in ../generator/measurement_3/*; do
	python3 measurement.py --wait-time 20 --config $i;
done
