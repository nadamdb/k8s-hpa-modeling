import argparse
import csv

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="Filename")
args = parser.parse_args()

freq = {}
with open(args.file) as f:
    reader = csv.reader(f)
    for row in reader:
        freq[row[0]] = freq.get(row[0], 0) + int(row[1])
sorted_freq = sorted(freq.items(), key=lambda kv: kv[1], reverse=True)
for k, v in sorted_freq:
    print("{}\t{}".format(k,v))
