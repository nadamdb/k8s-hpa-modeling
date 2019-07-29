#!/bin/bash
cat nodejs_app.yaml > live_nodejs_app.yaml
sed -i "s/\[POD_COUNT\]/$1/g" live_nodejs_app.yaml
sed -i "s/\[CPU\]/$2/g" live_nodejs_app.yaml
kubectl apply -f live_nodejs_app.yaml
