curl -g 'http://10.106.36.184:9090/api/v1/query?query=http_requests_total{job="apiserver"}[5m]' | python3 -m json.tool
