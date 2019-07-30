import requests
import json

res = json.loads(requests.get(url="http://10.103.164.29:8080/fortio/?labels=Fortio&url=http://172.16.0.7:30044&qps=1000&t=60s&n=&c=60000&p=50, 75, 90, 99, 99.9&r=0.0001&H=Host: nodejs-cpu-app&H=User-Agent: fortio.org/fortio-1.3.2-pre&H=&H=&H=&runner=http&resolve=&grpc-ping-delay=0&json=on&save=on&load=Start&timeout=100ms").text)

print(res)
