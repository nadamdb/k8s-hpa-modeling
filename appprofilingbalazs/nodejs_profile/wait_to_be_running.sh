#!/bin/bash

count=0
max_count=0
max_wait=60
round=0
echo 'Waiting for pods to be ready..'
while [ $count != $1 -o $count != $max_count -a $round != $max_wait ]
do
   round=$((round+1))
   count=`kubectl get pods | grep "\(fortio-deploy-$2\|nodejs-app-$2\).*" | awk '{print \$3}' | grep Running | wc -l`
   max_count=`kubectl get pods | grep "\(fortio-deploy-$2\|nodejs-app-$2\).*" | awk '{print \$3}' | wc -l`
   echo "Status: Running: $count/$1 , All Pods: $max_count"
   sleep 1
done

