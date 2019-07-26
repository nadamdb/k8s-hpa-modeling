#!/bin/bash

python3 -u mlhpacomponent/run.py --model lstm > lstm_prediction_facebook_du.log &
MLHPA_PID=$!
echo "Waiting..."
sleep 20
kubectl apply -f nodejs_mlhpa.yaml
echo "Waiting..."
sleep 20
echo "Measurement start."
python3 measurement_ml.py --type lstm --wait-time 15 --load ../generator/real_data/dobreff/Facebook_dest_du.json
kill $MLHPA_PID
kubectl delete -f nodejs_mlhpa.yaml
echo "Waiting..."
sleep 20
