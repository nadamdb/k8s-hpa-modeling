#!/bin/bash

#$1 measurement id
cat fortio.yaml > "fortio_live_$1.yaml"
sed -i "s/\[ID\]/$1/g" "fortio_live_$1.yaml"

kubectl create -f "fortio_live_$1.yaml"