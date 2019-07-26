#!/bin/bash

python3 mlhpacomponent/run.py --model lstm --logfile lstm_prediction_facebook_de.log &
MLHPA_PID=$!
kubectl apply -f nodejs_mlhpa.yaml
echo "Waiting..."
sleep 20
echo "Measurement start."
python3 measurement.py --type lstm --wait-time 1 --load ../generator/real_data/dobreff/Facebook_dest_de.json
#echo "Waiting..."
#sleep 20
kill $MLHPA_PID
kubectl delete -f nodejs_mlhpa.yaml
echo "Waiting..."
sleep 20
