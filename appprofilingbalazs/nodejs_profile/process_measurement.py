import json
import matplotlib.pyplot as plt

def plot_profile(measurement_res,x_axis,y_axis):
    all_cpus=[]
    all_qps=[]
    all_data = []
    for round in measurement_res:
        cpus=[]
        qps=[]
        cpus_max=[]
        data=[]
        for value in round['values'][:-1]:
            print('QPS: {0}; AVG_CPU: {1}'.format(value['qps'],value['avg_cpu']))
            cpus.append(value['avg_cpu'])
            qps.append(value['qps'])
            data.append({'cpu':value['avg_cpu']/float(round['pod']),'qps':value['qps']})
            #cpu_max=0
            #for cpu_value in value['cpu_values']:
            #    cpu_curr = float(cpu_value[1])
            #    cpu_max = cpu_max if cpu_curr < cpu_max else cpu_curr
            #cpus_max.append(cpu_max)
        newlist = sorted(data, key=lambda k: k[x_axis])
        x = [item[x_axis] for item in newlist]
        y = [item[y_axis] for item in newlist]
        print(newlist)
        plt.plot(x,y,'o-',label='POD: {0} / CPU: {1}'.format(round['pod'],round['cpu']))
        #plt.plot(qps,cpus,'o-',label='POD: {0} / CPU: {1}'.format(round['pod'],round['cpu']))
        #plt.plot(qps,cpus_max,'x-',label='POD: {0} / CPU: {1}'.format(round['pod'],round['cpu']))
        all_cpus.append(cpus)
        all_qps.append(qps)
        all_data.append(data)
        
    plt.ylabel('cpu')
    plt.xlabel('qps')
    plt.legend()
    plt.show()
    

with open('./19_07_16_16_53_09.json','r') as measurement:
    measurement_res = json.load(measurement)
    plot_profile(measurement_res,'qps','cpu')
    plot_profile(measurement_res,'cpu','qps')
