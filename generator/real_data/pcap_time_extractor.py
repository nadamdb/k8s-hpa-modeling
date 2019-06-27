import pandas as pd
import time
import os
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="Filename")
args = parser.parse_args()

start = time.time()
os.system("rm -f tmp.csv")
os.system("tshark -r {} -T fields -e frame.number -e frame.time_epoch -e ip.src -e ip.dst \
           -E header=y -E separator=, -E quote=d -E occurrence=f -Y \"tcp.port==443 || tcp.port==80\" \
           > tmp.csv".format(args.file))

df = pd.read_csv("tmp.csv", header=0, names=["num", "time", "ip_src", "ip_dst"])
#df = pd.read_csv(args.file, header=0, names=["num", "time", "ip_src", "ip_dst"])

top_ips = {"top1" : "152.66.89.44",
           "top2" : "10.4.4.17",
           "top3" : "10.4.4.20",
           "top4" : "10.4.4.19",
           "top5" : "152.66.150.170",
           "top6" : "152.66.57.222",
           "top7" : "152.66.26.201",
           "top8" : "152.66.79.165",
           "top9" : "152.66.130.255",
           "top10" : "152.66.57.178"}

data = {}

for rank, ip in top_ips.items():
    fdf = df[df["ip_dst"] == ip]
    data[rank] = fdf["time"].to_list()

os.system("mkdir -p times_per_file")
with open("times_per_file/" + os.path.basename(args.file) + "_top_ip_times.json", "w") as f:
    json.dump(data, f)

os.system("rm -f tmp.csv")
end = time.time()
print(end - start)
