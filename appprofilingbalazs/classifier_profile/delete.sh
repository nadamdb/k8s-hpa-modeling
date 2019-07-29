#!/bin/bash

#clear fortio
echo "delete fortio.."
cd fortio/ && ./delete.sh && cd ..
#clear nodejs
echo "delete nodejs_app.."
cd nodejs_app/ && ./delete.sh && cd ..
#clear lables
echo "remove labels"
kubectl label nodes --all type-
