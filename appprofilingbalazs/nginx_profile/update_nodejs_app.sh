#!/bin/bash
kubectl scale deployment nodejs-app --replicas=0
./wait_to_be_running.sh 1
cd nodejs_app/
./deploy.sh $1 $2
cd ..

