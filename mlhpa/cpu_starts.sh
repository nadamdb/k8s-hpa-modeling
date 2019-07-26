#!/bin/bash
./start_cpu_measurement_fb_du.sh
sleep 600
./start_cpu_measurement_all_du.sh
sleep 600
./start_cpu_measurement_fb_de.sh
sleep 600
./start_cpu_measurement_all_de.sh
