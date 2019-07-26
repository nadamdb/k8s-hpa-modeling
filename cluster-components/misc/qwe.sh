curl -g 'http://10.106.36.184:9090/api/v1/query?query=container_cpu_usage_seconds_total{container_name="test-server"}[1m]' | python3 -m json.tool
