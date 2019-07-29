#!/bin/bash

#$1 measrument id

kubectl delete -f "live_nodejs_app_$1.yaml"
