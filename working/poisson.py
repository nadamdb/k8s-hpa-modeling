#!/usr/bin/python3

import time, os, argparse, json
import numpy as np
from datetime import datetime

# Parsing arguments
parser = argparse.ArgumentParser()
parser.add_argument("--load-rate", help="Rate for the poisson load generation [rate = req/s]", type=int)
parser.add_argument("--length", help="Length of the measurements [min]", type=int)
parser.add_argument("--wait-time", help="Waiting time after the last request was sent [min]", type=int)

args = parser.parse_args()

# rate = req/sec
load_rate = args.load_rate

# [easurement_length] = sec
measurement_length = args.length * 60

wait_time = args.wait_time

start_time = time.time()
i = 0

timestamp = datetime.now()
timestamp = str(timestamp).replace(" ", "_").replace(":", "-")

# json logging
log = {}
log["timestamp"] = timestamp
log["load_rate"] = load_rate
log["length"] = measurement_length
log["wait"] = wait_time
log["start_time"] = start_time

'''while(time.time() < start_time + measurement_length): 
    os.system('curl "localhost:30884/exponential_serving?id=${i}&rate=2" &')
    print("SENT_" + str(i))
    time.sleep(np.random.exponential(1/load_rate))
    i += 1
'''
requests_sent_time = time.time()
log["requests_sent_time"] = requests_sent_time
print("********  All requests has been sent  ********")

print("********  Waiting starts  ********")
while(time.time() < requests_sent_time + wait_time):
    time.sleep(1)

end_time = time.time()
log["end_time"] = end_time
print("********  Measurements ended  ********")

with open("load_rate_" + str(load_rate) + "_length_" + str(args.length) + "_" + timestamp + ".metadata", "w") as file:
    json.dump(log, file)
