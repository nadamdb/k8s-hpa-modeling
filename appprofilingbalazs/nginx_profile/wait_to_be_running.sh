#!/bin/bash

count=0
max_count=0
echo 'Waiting for pods to be ready..'
while [ $count != $1 -o $count != $max_count ]
do
   count=`kubectl get pods | grep '\(fortio-deploy\|nodejs-app\).*' | awk '{print \$3}' | grep Running | wc -l`
   max_count=`kubectl get pods | grep '\(fortio-deploy\|nodejs-app\).*' | awk '{print \$3}' | wc -l`
   echo "Status: Running: $count/$1 , All Pods: $max_count"
   sleep 1
done

