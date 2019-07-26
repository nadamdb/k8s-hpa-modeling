from config import *
import time
import json
import requests
from threading import Thread
from stateLessLSTM import myLSTM
from ARmodel import myAR
import traceback
import argparse
import math

"""
---------------------------------------------------------------------------------------------------------
LSTM,AR:
1) Service started
2) Wait X time (1 hour) for the traces
3) pull X time window qps  num for prometheus and train the LSTM
4) from the train start timestamp to train end timestamp add the values to history
5) now we can forecast 
6) LSTM relearn 15 min; AR relearn 30 min

#) before each forecast we have to fill the history till now!
#) if 60 min in history forecast will predict the 61th value, addTsValue will add the 61th value to history
---------------------------------------------------------------------------------------------------------
QLearning:
Inputs: initial pod number; total qps/ actual pod num
---------------------------------------------------------------------------------------------------------
For each forecaster we have to grade its efficiency
---------------------------------------------------------------------------------------------------------
"""


class Service(object):
    def __init__(self, name, model, tradeoff):
        self.name = name
        if 'lstm' in model:
            self.model = myLSTM()
        elif 'ar' in model:
            self.model = myAR()
        self._creation_ts = int(time.time())
        self.last_value_ts = None
        self.last_training_ts = None
        self.last_forecast_ts = None
        self.predicted_values = dict()
        self.history_diffs = []
        self.forecast_enabled = False
        self.tradeoff = tradeoff
        self.grade = 0.0

    def train(self, data, nb_epochs=20, batchSize=32):
        self.last_training_ts = int(time.time())
        #print('{}  Training started'.format(str(self.last_training_ts)))
        self.model.train(tsData=data, nb_epochs=nb_epochs, batchSize=batchSize)
        #print('{}  Training finished'.format(str(int(time.time()))))
        self.get_values_till_now(self.last_training_ts)
        self.forecast_enabled = True

    def get_values_till_now(self, start_time, with_time=True):
        now = int(time.time())
        duration = int(now - start_time)
        while duration < 1:
            now = int(time.time())
            duration = int(now - start_time)
        duration = '{}s'.format(str(duration))
        raw_data = Connector.query_prometheus(
            query='rate(haproxy_backend_sessions_total[10s])[{1}:{0}]'.format(VALUE_TIME_INTERVAL_SEC, duration))
        while raw_data == '[]' or (type(raw_data) == list and len(raw_data) == 0):
            now = int(time.time())
            duration = int(now - start_time)
            duration = '{}s'.format(str(duration))
            raw_data = Connector.query_prometheus(
                query='rate(haproxy_backend_sessions_total[10s])[{1}:{0}]'.format(VALUE_TIME_INTERVAL_SEC, duration))
        data = Connector.parse(raw_data, with_time)
        #print('{0}  Filling history with duration: {1} values: {2}'.format(str(now), str(duration), str(data)))
        if not with_time:
            self.add_new_ts(data)
        else:
            self.add_new_ts([x[1] for x in data])

    def forecast(self):
        #print('Forecast started')
        self.get_values_till_now(self.last_value_ts)
        prediction = self.model.forecast()
        now = int(time.time())
        if prediction < 0:
            prediction = 0
        self.last_forecast_ts = now
        self.predicted_values[now+1] = prediction
        return now, prediction

    def add_new_ts(self, new_ts):
        self.last_value_ts = int(time.time())
        self.model.addTsValue(newTsVal=new_ts)

    def grade_service(self):
        now = int(time.time())
        #print('{0} Grading started'.format(now))
        duration = '{}s'.format(now - self.last_forecast_ts)
        raw_data = Connector.query_prometheus(
            query='rate(haproxy_backend_sessions_total[10s])[{1}:{0}]'.format(VALUE_TIME_INTERVAL_SEC, duration))
        while raw_data == '[]' or (type(raw_data) == list and len(raw_data) == 0):
            now = int(time.time())
            duration = '{}s'.format(now - self.last_forecast_ts)
            raw_data = Connector.query_prometheus(
                query='rate(haproxy_backend_sessions_total[10s])[{1}:{0}]'.format(VALUE_TIME_INTERVAL_SEC, duration))
            time.sleep(1)
        data = Connector.parse(raw_data, with_time=True)
        history_keys = [list(y.keys())[0] for y in self.history_diffs]
        prediction_keys = list(self.predicted_values.keys())
        for x in data:
            if x[0] not in history_keys and x[0] in prediction_keys:
                if self.predicted_values[x[0]] == 0 and x[1] == 0:
                    self.history_diffs.append({x[0]: 0.0})
                else:
                    pred = float(self.predicted_values[x[0]])
                    real = float(x[1])
                    self.history_diffs.append({x[0]: 2*((pred-real)/(abs(pred)+abs(real)))})
        self.grade = sum([list(x.values())[0] for x in self.history_diffs])/len(self.history_diffs)
        #print('{0} Grading finished grade: {1}'.format(int(time.time()), self.grade))


class Connector(object):

    def __init__(self, model):
        self.service = None
        self.model = model

    def create_service(self, label_value):
        service = Service(SERVICE_NAME, self.model, label_value)
        self.service = service

    def train_service(self, training_data):
        Thread(target=self.service.train, args=(training_data,)).start()

    def get_session_num(self, start_time=None):
        raw_data = '[]'
        while raw_data == '[]' or (type(raw_data) == list and len(raw_data) == 0):
            now = time.time()
            if start_time is None:
                duration = '{}s'.format(str(int(now-self.service._creation_ts)))
            else:
                duration = '{}s'.format(str(int(now-start_time)))
            query = 'rate(haproxy_backend_sessions_total[10s])[{1}:{0}]'.format(VALUE_TIME_INTERVAL_SEC, duration)
            raw_data = self.query_prometheus(query)
        data = self.parse(raw_data)
        #print('{0}  Received qps values: {1}'.format(str(int(time.time())), str(data)))
        return data

    @staticmethod
    def parse(data, with_time=False):
        for s in data:
            proxy = s['metric']['proxy']
            if SERVICE_NAME in proxy:
                if not with_time:
                    return [float(x[1]) for x in s['values']]
                else:
                    return [(int(x[0]), float(x[1])) for x in s['values']]

    @staticmethod
    def query_prometheus(query='kube_pod_info'):
        try:
            response = requests.get('http://{0}:{1}/api/v1/query'.format(PROMETHEUS_IP, PROMETHEUS_PORT),
                                    params={'query': query})
            results = response.json()['data']['result']
            return results
        except Exception:
            #traceback.print_exc()
            return '[]'

    def push(self, value, metric=METRIC_NAME):
        try:
            headers = {'Content-type': 'application/json'}
            response = requests.post(
                'http://{0}:{1}/write-metrics/namespaces/{2}/services/{3}/{4}'.format(HAPROXY_IP, HAPROX_PORT,
                                                                                      NAMESPACE, SERVICE_NAME,
                                                                                      metric),
                data='"{}"'.format(str(value)), headers=headers)
            #print(response)
            return response
        except Exception:
            #traceback.print_exc()
            return '[]'

    def run(self):
        push_time = 1
        waiting_time = WAITING_TIME_AFTER_CREATION_SEC
        # While there is no service object we just poll the prometheus for service name in every second
        while self.service is None:
            data = self.query_prometheus(query='kube_service_labels')
            data = [x for x in data if SERVICE_NAME in x['metric']['service']]
            for s in data:
                label_value = int(s['metric']['label_'+LABEL_NAME])
                if self.service is None:
                    self.create_service(label_value)
                    # time.sleep(WAITING_TIME_AFTER_CREATION_SEC)
                    # data = self.get_session_num()
                    # self.train_service(data)
            time.sleep(1)

        while waiting_time > 0:
            self.push(0)
            print("qps;{0};{1}".format(time.time(),0))
            self.push_cpu_metric()
            waiting_time -= 1
            time.sleep(1)
        data = self.get_session_num()
        self.train_service(data)
        time.sleep(1)

        # Service created we start the main loop
        while True:
            forecast_happened = False
            if not self.service.forecast_enabled:
                self.push(0)
                print("qps;{0};{1}".format(time.time(),0))
                self.push_cpu_metric()
            else:
                if push_time == 0:
                    forecast_time, forecasted_value = self.service.forecast()
                    #print('{0}  Predicted value: {1}'.format(str(forecast_time), forecasted_value))
                    #print('{0}  Tradeoff parameter: {1} -> Pushed value: {2}'.format(str(forecast_time),
                    #                                                                 self.service.tradeoff,
                    #                                                                 forecasted_value +
                    #                                                                 self.service.tradeoff))
                    if 0.0 - GRADE_THRESHOLD <= self.service.grade <= 0.0 + GRADE_THRESHOLD:
                        raw_data = '[]'
                        while raw_data == '[]' or (type(raw_data) == list and len(raw_data) == 0):
                            query = 'count(kube_pod_info{pod=~"'+DEPLOYMENT_NAME+'.*"})'
                            raw_data = self.query_prometheus(query)
                        pod_num = int(raw_data[0]['value'][1])
                        self.push(forecasted_value/pod_num*self.service.tradeoff)
                        print("qps;{0};{1}".format(time.time(),forecasted_value/pod_num*self.service.tradeoff))
                        self.push(0.0, metric=CPU_METRIC_NAME)
                        print("cpu;{0};{1}".format(time.time(),0))
                    else:
                        self.push(0)
                        print("qps;{0};{1}".format(time.time(),0))
                        self.push_cpu_metric()
                    push_time = 1
                    forecast_happened = True
                else:
                    push_time -= 1
                now = int(time.time())
                if now-self.service.last_training_ts >= (TRAINING_TIME_INTERVAL_MINUTES*60):
                    data = self.get_session_num(self.service.last_training_ts)
                    self.train_service(data)
            time.sleep(1)
            if forecast_happened:
                self.service.grade_service()

    def push_cpu_metric(self):
        raw_data = '[]'
        while raw_data == '[]' or (type(raw_data) == list and len(raw_data) == 0):
            query = '(sum(rate(container_cpu_usage_seconds_total{pod_name=~"'+DEPLOYMENT_NAME+'.*",container_name!="POD"}[1m])) / count(kube_pod_info{pod=~"'+DEPLOYMENT_NAME+'.*"})) * 1000'
            raw_data = self.query_prometheus(query)
        data = int(float(raw_data[0]['value'][1]) * (10**9))
        #print('{0}  Received CPU value: {1}'.format(str(int(time.time())), str(data)))
        print("cpu;{0};{1}".format(time.time(),data))
        self.push(data, metric=CPU_METRIC_NAME)


def main(model):
    connector = Connector(model)
    connector.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scaling predictor')
    parser.add_argument('--model', '-m', type=str, default='lstm', help='Set the machine learning model. It can be: lstm, ar')
    args = parser.parse_args()
    main(args.model)
