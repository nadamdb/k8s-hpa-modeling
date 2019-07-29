#!/bin/bash
sudo docker build -t balazska/nodejs_app:$1 .
sudo docker push balazska/nodejs_app:$1
