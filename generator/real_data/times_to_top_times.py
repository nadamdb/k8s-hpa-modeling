import json
import argparse
import time

start = time.time()

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="Filename")
args = parser.parse_args()

with open(args.file, "r") as f:
    d = f.read()

data = json.loads(d)

for i in range(1, 11):
    with open("times_per_top/top{}.times".format(str(i)), "a") as out:
        for t in data["top"+str(i)]:
            out.write(str(t)+"\n")

end = time.time()
print(end-start)
