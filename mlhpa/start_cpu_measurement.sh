#!/bin/bash

kubectl apply -f nodejs_cpuhpa.yaml
echo "Waiting..."
sleep 10
echo "Measurement start."
python3 measurement.py --type cpu --wait-time 1 --load ../generator/real_data/dobreff/Facebook_dest_de.json
echo "Waiting..."
sleep 10
kubectl delete -f nodejs_cpuhpa.yaml
