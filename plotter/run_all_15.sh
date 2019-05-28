for i in {4,8,,12,16,20}; do python3 plotter.py --k8s-log ../working/1h_15s/load_rate_$i* --model-log ../discrete_model/1h_15s_other/arrival_rate_$i*; done
