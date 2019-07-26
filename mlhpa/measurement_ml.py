#!/usr/bin/python3

import time, os, argparse, json
import numpy as np
from prometheuscollector_cpuhpa import PrometheusCollector as PrometheusCollectorCPU
from prometheuscollector_mlhpa import PrometheusCollector as PrometheusCollectorML
from datetime import datetime
import ntpath

# Parsing arguments
parser = argparse.ArgumentParser()
parser.add_argument("--type", help="ML or classic CPU HPA [lstm/ar/cpu]")
parser.add_argument("--wait-time", help="Waiting time after the last request was sent [min]", type=int)
parser.add_argument("--load", help="Load file for the measurement")

args = parser.parse_args()

with open(args.load, "r") as f:
    log = json.load(f)
if log is None:
    raise FileNotFoundError
load_wait_times = log["data"]["load_wait_time"]
metadata = log["metadata"]

if args.type == "cpu":
    ML = False
else:
    ML = True

to_file = "{0}_hpa_{1}_wait_time_{2}".format(args.type, ntpath.basename(args.load)[:-5], str(args.wait_time))

wait_time = args.wait_time * 60

start_time = time.time()

timestamp = datetime.now()
timestamp = str(timestamp).replace(" ", "_").replace(":", "-")

# json logging
log = {}
metadata["timestamp"] = timestamp
metadata["wait"] = args.wait_time
metadata["start_time"] = start_time
metadata["hpa_type"] = args.type

for i in range(0, len(load_wait_times) + 1):
    if ML:
        command = 'curl -H "Host: nodejs-ml-app" http://172.16.0.7:30044'
    else:
        command = 'curl -H "Host: nodejs-cpu-app" http://172.16.0.7:30044'
    os.system(command + ' &')
    print("SENT_" + str(i))
######
#    if i == 1000:
#        break
######
    if i < len(load_wait_times):
        time.sleep(load_wait_times[i])

requests_sent_time = time.time()
metadata["requests_sent_time"] = requests_sent_time
print("********  All requests has been sent  ********")

print("********  Waiting starts  ********")
while time.time() < requests_sent_time + wait_time:
    time.sleep(1)

end_time = time.time()
metadata["end_time"] = end_time
print("********  Measurement ended  ********")

log["metadata"] = metadata

if ML:
    pc = PrometheusCollectorML(log)
else:
    pc = PrometheusCollectorCPU(log)

log = pc.collect_logs()

with open(to_file + "_timestamp_" + timestamp + ".log", "w") as file:
    json.dump(log, file)
