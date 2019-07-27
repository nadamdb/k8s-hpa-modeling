#!/bin/bash

python3 -u armlhpacomponent/run.py --model ar > ar_prediction_facebook_du.log &
MLHPA_PID=$!
echo "Waiting..."
sleep 20
kubectl apply -f nodejs_armlhpa.yaml
echo "Waiting..."
sleep 20
echo "Measurement start."
python3 measurement_arml.py --type ar --wait-time 15 --load ../generator/real_data/dobreff/Facebook_dest_du.json
kill $MLHPA_PID
kubectl delete -f nodejs_armlhpa.yaml
echo "Waiting..."
sleep 20
