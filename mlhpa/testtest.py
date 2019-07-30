import os
import time

s = time.time()
for i in range(0, 1):
    os.system('curl -I --no-keepalive -s -o /dev/null -H "Host: nodejs-cpu-app" http://172.16.0.7:30044 &')
    #os.system('wget -t 1 -q -b --timeout 0.1 --no-http-keep-alive -O /dev/null --header "Host: nodejs-cpu-app" http://172.16.0.7:30044')
    time.sleep(0.001)
e = time.time()
print(e-s)
