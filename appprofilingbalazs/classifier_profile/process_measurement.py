import json
import matplotlib.pyplot as plt

with open('./19_07_04_08_59_26.json','r') as measurement:
    measurement_res = json.load(measurement)
    for round in measurement_res:
        cpus=[]
        qps=[]
        for value in round['values'][:-1]:
            print('QPS: {0}; AVG_CPU: {1}'.format(value['qps'],value['avg_cpu']))
            cpus.append(value['avg_cpu'] / int(round['pod']))
            qps.append(value['qps'])
        plt.plot(qps,cpus,'o-',label='POD: {0} / CPU: {1}'.format(round['pod'],round['cpu']))
    plt.ylabel('avg cpu usage')
    plt.xlabel('qps')
    plt.legend()
    plt.show()
    for round in measurement_res:
        cpus=[]
        qps=[]
        for value in round['values'][:-1]:
            print('QPS: {0}; AVG_MEM: {1}'.format(value['qps'],value['avg_mem']))
            cpus.append(value['avg_mem'] / int(round['pod']))
            qps.append(value['qps'])
        plt.plot(qps,cpus,'o-',label='POD: {0} / CPU: {1}'.format(round['pod'],round['cpu']))
    plt.ylabel('avg mem usage')
    plt.xlabel('qps')
    plt.legend()
    plt.show()