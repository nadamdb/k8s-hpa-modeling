#!/bin/bash
kubectl scale deployment nodejs-app-$3 --replicas=0
./wait_to_be_running.sh 1 $3 
cd nodejs_app/
./deploy.sh $1 $2 "live_nodejs_app_$3.yaml" $3
cd ..

