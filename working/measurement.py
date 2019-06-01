#!/usr/bin/python3

import time, os, argparse, json
import numpy as np
from prometheuscollector import PrometheusCollector
from datetime import datetime

import importlib.util
spec = importlib.util.spec_from_file_location("timegenerator", "../generator/timegenerator.py")
timegenerator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timegenerator)

# Parsing arguments
parser = argparse.ArgumentParser()
parser.add_argument("--load-rate", help="Rate for the poisson load generation [rate = req/s]", type=int)
parser.add_argument("--serve-rate", help="Rate for the exponential serve times [rate = req/s]", type=int)
parser.add_argument("--length", help="Length of the measurement [min]", type=int)
parser.add_argument("--wait-time", help="Waiting time after the last request was sent [min]", type=int)
parser.add_argument("--config", help="Config log file for the measurement")

args = parser.parse_args()

load_wait_times = []
serve_times = []
metadata = {}

if args.config is not None:
    _, load_wait_times, serve_times, metadata = timegenerator.load_times_from_file(args.config)
else:
    load_generator = timegenerator.PoissonLoadGenerator(args.load_rate, args.length)
    load_send_times = load_generator.get_send_times()
    load_wait_times = load_generator.get_wait_times()

    serve_times = timegenerator.generate_serve_times(len(load_send_times), args.serve_rate)

    metadata = {"measurement_length": args.length, "load_rate": args.load_rate, "serve_rate": args.serve_rate}

to_file = "k8s_measurement_length_" + str(metadata["measurement_length"]) + \
                    "min_load_rate_" + str(metadata["load_rate"]) + \
                    "_serve_rate_" + str(metadata["serve_rate"])
if args.config is not None:
    to_file += "_random_seed_" + str(metadata["random_seed"])

# rate = req/sec
load_rate = metadata["load_rate"]

# [measurement_length] = sec
measurement_length = metadata["measurement_length"] * 60

wait_time = args.wait_time * 60

start_time = time.time()

timestamp = datetime.now()
timestamp = str(timestamp).replace(" ", "_").replace(":", "-")

# json logging
log = {}
metadata["timestamp"] = timestamp
# metadata["load_rate"] = load_rate
# metadata["length"] = measurement_length
metadata["wait"] = args.wait_time
metadata["start_time"] = start_time

# i = 0
# while(time.time() < start_time + measurement_length):
#     os.system('curl "localhost:30884/exponential_serving?id=${i}&rate=2" &')
#     print("SENT_" + str(i))
#     time.sleep(np.random.exponential(1/load_rate))
#     i += 1
for i in range(0, len(serve_times)):
    serve = serve_times[i]
    curl_string = "localhost:30884/fixed_serving?id=" + str(i) + "&wait=" + str(serve)
    os.system('curl "' + curl_string + '" &')
    print("SENT_" + str(i))
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

pc = PrometheusCollector(log)
log = pc.collect_logs()

with open(to_file + "_timestamp_" + timestamp + ".log", "w") as file:
    json.dump(log, file)
