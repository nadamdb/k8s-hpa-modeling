#!/bin/bash

#$1 measurement id

#clear fortio
echo "delete fortio.."
cd fortio/ && ./delete.sh $1 && cd ..
#clear nodejs
echo "delete nodejs_app.."
cd nodejs_app/ && ./delete.sh $1 && cd ..
#clear lables
#echo "remove labels"
#kubectl label nodes --all type-
