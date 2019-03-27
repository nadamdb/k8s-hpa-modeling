#!/bin/bash
kubectl delete -f model.yaml
kubectl delete hpa model-deployment
