#!/bin/bash

kubectl create -f daemonset.yaml
COUNT=0
while [ $COUNT -ne 3 ]
do
   COUNT=$(kubectl get pods | grep "log-collector" | awk '{print $3}' | sed 's/Running/Running/' | grep "^Running$" | wc -l)
   sleep 1
done
echo "Daemonset pods are ready"
for pod in `kubectl get pods | grep "log-collector" | awk '{print $1}'`; do
   echo $pod
   kubectl exec -it $pod -- bash -c "> /media/server.log"
   kubectl exec -it $pod -- bash -c "cat /media/server.log"
done

kubectl delete -f daemonset.yaml

