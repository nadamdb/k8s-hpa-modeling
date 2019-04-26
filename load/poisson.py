#!/usr/bin/python3

import time

import numpy
import os

rate = 12  #req/sec

#measurement_length = 120*60
measurement_length = 1*60
start_time = time.time()

while(time.time() < start_time + measurement_length):
#for i in range(1,2000):
   os.system('curl "localhost:30884/exponential_serving?id=${i}&rate=2" &')
#   print('SENT')
   time.sleep(numpy.random.exponential(1/rate))
