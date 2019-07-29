#!/bin/bash

python3 measurement.py 1 &
f=$!
python3 measurement.py 2 &
s=$!
#python3 measurement.py 3 &
#t=$!

echo "$f $s" > ps
#echo "$f" > ps

#wait $f $s $t
wait $f $s
echo "DONE" 
