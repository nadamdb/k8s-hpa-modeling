#!/bin/bash

for ((i=1;i<=480;i++)); do
	sleep 0.25
	echo "$i;`date "+%H:%M:%S:%N"`" | sed 's/......$//' >> example.local
	curl "localhost:31165/exponential_serving?id=$i&rate=2" &
done

