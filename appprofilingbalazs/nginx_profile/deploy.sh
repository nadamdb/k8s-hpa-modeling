#!/bin/bash

#we need node names here
sut=$1
benchmark=$2

#$3 - POD_COUNT
#$4 - CPU per pod

echo "create type labels for nodes.."
kubectl label nodes $1 type=sut
kubectl label nodes $2 type=benchmark
echo "install nodejs app"
cd nodejs_app/ && ./deploy.sh $3 $4
cd ..
echo "get service ip"
service_ip=`kubectl get services | grep nodejs-service | awk '{print \$3}'`
echo $service_ip
echo "install fortio"
cd fortio/ && ./deploy.sh
cd ..
echo "get fortio ip"
fortio_ip=`kubectl get services | grep fortio | awk '{print \$3}'`
echo $fortio_ip

cat config.yaml > live_config.yaml
sed -i "s/\[SERVICE_IP\]/$service_ip/g" live_config.yaml
sed -i "s/\[FORTIO_IP\]/$fortio_ip/g" live_config.yaml
