curl -g 'http://10.106.36.184:9090/api/v1/query?query=container_cpu_usage_seconds_total{namespace="default"}[5m]' | python3 -m json.tool
#curl -g 'http://10.106.36.184:9090/api/v1/label/__name__/values' | python3 -m json.tool


