import requests
from mlhpacomponent.config import *

query = "kube_service_labels"
response = requests.get('http://{0}:{1}/api/v1/query'.format(PROMETHEUS_IP, PROMETHEUS_PORT), params={'query': query})
print(response)
