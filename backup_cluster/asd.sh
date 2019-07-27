#!/bin/bash
cd custom-metrics_export
./buc.sh
cd ../default_export
./buc.sh
cd ../haproxy-controller_export
./buc.sh
cd ../kube-public_export
./buc.sh
cd ../kube-system_export
/buc.sh
cd ../monitoring_export
./buc.sh
