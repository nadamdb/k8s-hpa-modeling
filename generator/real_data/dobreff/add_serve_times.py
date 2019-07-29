import argparse, json, ntpath
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("--load", help="Load file for the measurement")
parser.add_argument("--serve-rate", help="Serve rate", type=int)

args = parser.parse_args()

with open(args.load, "r") as f:
    log = json.load(f)

random = np.random.RandomState(seed=42)

serve_time = []

for _ in log["data"]["load_send_time"]:
    serve_time.append(random.exponential(1 / args.serve_rate))

log["data"]["serve_time"] = serve_time



with open(ntpath.basename(args.load)[:-5] + "_with_" + str(args.serve_rate) + "_serve_rate.json", "w") as file:
    json.dump(log, file)
