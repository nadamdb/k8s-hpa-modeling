#!/bin/bash

for ((i=1;i<=400;i++)); do
	sleep 1
	echo "$i;`date "+%H:%M:%S:%N"`" | sed 's/......$//' >> example.local
	curl "localhost:30820/exponential_serving?id=$i&rate=0.33" &
done
