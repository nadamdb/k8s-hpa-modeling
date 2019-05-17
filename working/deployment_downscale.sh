#!/bin/bash

COUNT=0
deployment=$(kubectl get deployments | grep 'model-deployment' | awk '{print $1}')
kubectl scale deployment $deployment --replicas=1
while [ $COUNT -ne 1 ]
do
   COUNT=$(kubectl get deployment | grep 'model-deployment' | awk '{print $3}')
   sleep 1
done
