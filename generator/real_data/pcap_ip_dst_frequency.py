import pandas as pd
import argparse
import os
import time

start = time.time()
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="Filename")
args = parser.parse_args()

os.system("rm -f tmp.csv")
os.system("tshark -r {} -T fields -e ip.dst \
           -E header=y -E separator=, -E quote=d -E occurrence=f -Y \"tcp.port==443 || tcp.port==80\" \
           > tmp.csv".format(args.file))

df = pd.read_csv("tmp.csv", header=0, names=["ip_dst"])
#df = pd.read_csv(args.file, header=0, names=["num", "time", "ip_src", "ip_dst"])

os.system("mkdir -p ip_dst_frequencies")
df["ip_dst"].value_counts().to_csv("ip_dst_frequencies/" + os.path.basename(args.file)  + "_ip_dst_frequency.out", header=False)

os.system("rm -f tmp.csv")
end = time.time()
print(end - start)
