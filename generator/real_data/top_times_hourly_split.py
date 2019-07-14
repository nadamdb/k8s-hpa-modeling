import argparse
import json
import os
import time
import numpy as np

start_time = time.time()

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="Filename")
args = parser.parse_args()

random_seed = 0
random = np.random.RandomState(seed=random_seed)

with open(args.file, "r") as f:
    hour = 1
    h = []
    while True:
        if hour == 11:
            break
        line = f.readline()
        if not line:
            dir = "times_per_top_hourly/"+os.path.basename(args.file)[:-6]
            os.system("mkdir -p "+dir)

            start = h[0]
            h_send = [x-start for x in h]
            h_wait = []
            for i in range(1,len(h)):
                h_wait.append(h[i] - h[i-1])
            
            for serve in [2,8]:
                log = {"metadata":{"origin":args.file, "hour":hour, "serve_rate":serve, "random_seed":random_seed, "type":"real"}}
                serve_times = []
                for s in range(0, len(h_send)):
                    serve_times.append(random.exponential(1 / serve))
                data = {"load_send_times":h_send, "load_wait_times":h_wait, "load_original":h, "serve_times":serve_times}
                log["data"] = data
                    
                with open("{}/{}_serve_rate_{}.json".format(dir,str(hour),serve), "w") as out:
                    json.dump(log, out)

            h = []
            hour += 1
            break
        line = float(line.strip())
        if len(h) == 0:
            h.append(line)
        elif line - h[0] <= 3600:
            h.append(line)
        else:
            dir = "times_per_top_hourly/"+os.path.basename(args.file)[:-6]
            os.system("mkdir -p "+dir)

            start = h[0]
            h_send = [x-start for x in h]
            h_wait = []
            for i in range(1,len(h)):
                h_wait.append(h[i] - h[i-1])
            
            for serve in [2,8]:
                log = {"metadata":{"origin":args.file, "hour":hour, "serve_rate":serve, "random_seed":random_seed, "type":"real"}}
                serve_times = []
                for s in range(0, len(h_send)):
                    serve_times.append(random.exponential(1 / serve))
                data = {"load_send_times":h_send, "load_wait_times":h_wait, "load_original":h, "serve_times":serve_times}
                log["data"] = data
                    
                with open("{}/{}_serve_rate_{}.json".format(dir,str(hour),serve), "w") as out:
                    json.dump(log, out)

            h = []
            hour += 1

print(time.time()-start_time)
