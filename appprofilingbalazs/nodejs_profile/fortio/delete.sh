#!/bin/bash
#$1 measurement id

kubectl delete -f "fortio_live_$1.yaml"