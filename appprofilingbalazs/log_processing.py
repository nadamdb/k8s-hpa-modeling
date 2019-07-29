import json
import matplotlib.pyplot as plt
from os import listdir
from os.path import isfile, join
import numpy
from numpy.polynomial.polynomial import polyfit


def plot_profile(folder,x_axis,y_axis):
    
    onlyfiles = [f for f in listdir(folder) if isfile(join(folder, f))]
    print(onlyfiles)
    m_s = []
    for file in onlyfiles:
        x_pod = []
        y_pod = []

        y_0s = []
        with open(join(folder, file),'r') as measurement:
            round = json.load(measurement)
            all_cpus=[]
            all_qps=[]
            all_data = []
            cpus=[]
            qps=[]
            cpus_max=[]
            data=[]
            for value in round['values'][:-1]:
                #print('QPS: {0}; AVG_CPU: {1}'.format(value['qps'],value['avg_cpu']))
                cpus.append(value['avg_cpu'])
                qps.append(value['qps'])
                if(value['avg_cpu'] != 'N/A' and value['req_lost']<10):
                    cpu_values=value['cpu_values']
                    cpu_usage_array =[]
                    transient = True
                    for cpu_usage in cpu_values:
                        cpu_usage_info = float(cpu_usage[1])
                        if (cpu_usage_info > 0.000000000000001):
                            transient = False 
                            cpu_usage_array.append(cpu_usage_info)
                        if cpu_usage_info < 0.000000000000001 and not transient:
                            cpu_usage_array.append(cpu_usage_info)
                    #data.append({'cpu':value['avg_cpu'],'qps':value['qps']})
                    data.append({'cpu':numpy.average(cpu_usage_array)*10,'qps':value['qps']})
                #cpu_max=0
                #for cpu_value in value['cpu_values']:
                #    cpu_curr = float(cpu_value[1])
                #    cpu_max = cpu_max if cpu_curr < cpu_max else cpu_curr
                #cpus_max.append(cpu_max)
            newlist = sorted(data, key=lambda k: k[x_axis])
            x = [item[x_axis] for item in newlist]
            y = [item[y_axis] for item in newlist]

            # Fit with polyfit
            p = numpy.poly1d(numpy.polyfit(x,y,1))
            y1 = p(x)

            m =  (y[1]-y[0])/(x[1]-x[0])
            m_s.append(m)
            y_0s.append(y[0])
            print(" m = {0}".format(m))

            #plt.plot(x, y1, '-',label='POD: {0} / CPU: {1}'.format(round['pod'],round['cpu']))

            #update x_pod, y_pod



            plt.plot(x,y,'o-',label='POD: {0} / CPU: {1}'.format(round['pod'],round['cpu']))
            #plt.plot(qps,cpus,'o-',label='POD: {0} / CPU: {1}'.format(round['pod'],round['cpu']))
            #plt.plot(qps,cpus_max,'x-',label='POD: {0} / CPU: {1}'.format(round['pod'],round['cpu']))
            all_cpus.append(cpus)
            all_qps.append(qps)
            all_data.append(data)
    print(m_s)
    m_avg = numpy.average(m_s)
    print(m_avg)
    y_0avg = numpy.average(y_0s)
    print(y_0avg)

    x_model = all_qps[0]
    print(x_model)
    y_avg = [ m_avg*float(x)+y_0avg for x in x_model]

    #plt.plot(x_model, y_avg, '-',label='Calculated linear relation'.format(round['pod'],round['cpu']))

    cpu_request = 1
    max_pod = 5

    steps = [ (i+1) * cpu_request for i in range(0,max_pod)]
    print(steps)

    x_pods = []
    y_pods = []
    initpod = 1
    x0=0
    for step in steps:
        x_pods.append(x0)
        y = initpod
        y_pods.append(y)
        y_pods.append(y)
        x0 = (step - y_0avg) / m_avg
        initpod+=1
        x_pods.append(x0)
    print(x_pods)
    plt.plot(x_pods, y_pods, '-',label='Calculated linear relation POD/QPS')

    plt.ylabel(y_axis)
    plt.xlabel(x_axis)
    plt.legend()
    plt.show()
    
## NODEJS 

#plot_profile('./nodejs_profile/logs/nodejs_3','qps','cpu')
#plot_profile(measurement_res,'cpu','qps')
#plot_profile('./nodejs_profile/logs/nodejs_3','cpu','qps')


## Classification

#plot_profile('./nodejs_profile/logs/nodejs_5_profile','qps','cpu')
#plot_profile(measurement_res,'cpu','qps')
#plot_profile('./nodejs_profile/logs/nodejs_5_profile','cpu','qps')

## NGINX

plot_profile('./nodejs_profile/logs/nodejs_7_profile','qps','cpu')
#plot_profile(measurement_res,'cpu','qps')
#plot_profile('./nginx_profile/logs/nginx_2','cpu','qps')