#!/bin/bash

kubectl apply -f nodejs_cpuhpa.yaml
echo "Waiting..."
sleep 20
echo "Measurement start."
python3 measurement.py --type cpu --wait-time 15 --load ../generator/real_data/dobreff/Facebook_dest_du.json
kubectl delete -f nodejs_cpuhpa.yaml
echo "Waiting..."
sleep 20
