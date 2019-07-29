#!/bin/bash
#$1 POD COUNT
#$2 CPU PER POD
#$3 LIVE CONFIG FILENAME
#$4 MEASUREMENT ID

cat nodejs_app.yaml > $3
sed -i "s/\[POD_COUNT\]/$1/g" $3
sed -i "s/\[CPU\]/$2/g" $3
sed -i "s/\[ID\]/$4/g" $3
kubectl apply -f $3
