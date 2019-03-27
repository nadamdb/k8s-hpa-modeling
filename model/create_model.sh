#!/bin/bash
kubectl create -f model.yaml
kubectl autoscale deployment model-deployment --cpu-percent=50 --min=1 --max=10
