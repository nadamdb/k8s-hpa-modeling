#!/bin/bash
./start_ml_ar_measurement_all_du.sh
sleep 600
./start_ml_ar_measurement_fb_du.sh
sleep 600
./start_ml_ar_measurement_all_de.sh
sleep 600
./start_ml_ar_measurement_fb_de.sh
