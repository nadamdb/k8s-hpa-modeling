#!/usr/bin/python3

import time

import numpy
import os

rate = 4  #req/sec

for i in range(1,2000):
   os.system('curl "localhost:31165/exponential_serving?id=${i}&rate=2" &')
   print('SENT')
   time.sleep(numpy.random.exponential(1/rate))
