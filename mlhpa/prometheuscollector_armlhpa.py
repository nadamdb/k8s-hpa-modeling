#!/usr/bin/python3

import requests
import json
import urllib.parse as up
# curl -g 'http://10.106.36.184:9090/api/v1/query?query=count(kube_pod_info{namespace="default"})[60s:1s]&time=1556960632' | python3 -m json.tool


class PrometheusCollector:
    def __init__(self, log):
        self.log = log
        self.log["data"] = {}
        self.time = int(log["metadata"]["end_time"])
        self.duration = int(self.time - log["metadata"]["start_time"])

    def collect_logs(self):
        self.log["data"]["hpa_current"] = self.get_json_values("kube_hpa_status_current_replicas{hpa=\"nodejs-arml-hpa\"}")
        self.log["data"]["hpa_desired"] = self.get_json_values("kube_hpa_status_desired_replicas{hpa=\"nodejs-arml-hpa\"}")
        self.log["data"]["pod_count"] = self.get_json_values("count(kube_pod_info{pod=~\"nodejs-arml-deployment.*\"})")
        self.log["data"]["cpu_percentage"] = self.get_json_values("(sum(rate(container_cpu_usage_seconds_total{pod_name=~\"nodejs-arml-deployment.*\",container_name!=\"POD\"}[1m])) / count(kube_pod_info{pod=~\"nodejs-arml-deployment.*\"}) * 1000)")
        self.log["data"]["cpu_hpa"] = self.get_json_values("sum(rate(container_cpu_usage_seconds_total{pod_name=~\"nodejs-arml-deployment.*\",container_name!=\"POD\"}[1m]))")
        self.log["data"]["qps"] = self.get_json_values("rate(haproxy_backend_sessions_total{proxy=\"default-nodejs-arml-service-3000\"}[10s])")
        self.log["data"]["response_error"] = self.get_json_values("rate(haproxy_backend_response_errors_total{proxy=\"default-nodejs-arml-service-3000\"}[10s])")
        self.log["data"]["connection_error"] = self.get_json_values("rate(haproxy_backend_connection_errors_total{proxy=\"default-nodejs-arml-service-3000\"}[10s])")
        return self.log

    def get_json_values(self, metric):
        full_query = up.quote(metric + "[" + str(self.duration) + "s:1s]")
        full_url = "http://10.42.0.9:9090/api/v1/query?query=" + full_query + "&time=" + str(self.time)
        full_json = requests.get(url = full_url).json()
        return full_json["data"]["result"][0]["values"]


if __name__ == "__main__":
    log = {"metadata": {"timestamp": "2019-05-04_11-04-58.496242", "load_rate": 2, "length": 60, "wait": 0, "start_time":1564139869.1704335 , "requests_sent_time": 1556967898.4962623, "end_time":1564139929.1704335 }}
    pc = PrometheusCollector(log)
    print(json.dumps(pc.collect_logs()))

