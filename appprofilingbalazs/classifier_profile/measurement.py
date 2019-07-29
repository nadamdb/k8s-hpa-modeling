import json
import subprocess
import yaml
import requests
import time
import numpy
import datetime

with open('config.yaml') as config_file:
    config = yaml.safe_load(config_file)
    max_cpu = str(config['measurement']['max_cpu'])
    cpus = config['measurement']['cpus']
    max_pod = len(cpus)

    #load benchmark config
    start_qps = config['measurement']['start_qps']
    start_qps = start_qps if int(start_qps) != 0 else 1 
    step = config['measurement']['step']
    max_benchmark_iteration = config['measurement']['max_benchmark']
    max_request_lost = config['measurement']['max_request_lost']
    benchmark_time = config['measurement']['benchmark_time']

    print('\n-------------- Nodejs App Profiler --------------\n')
    print('Deploy nodejs app to {0}'.format(config['deploy']['sut_worker']))
    print('Deploy Fortio to {0}'.format(config['deploy']['benchmark_worker']))
    print('MAX Pod count: {0}, Max CPU resource: {1}'.format(max_pod,max_cpu))
    print('--------------------------------------------------\n')
    print('-------------------- Start Deploy ----------------\n')
    subprocess.call(['./deploy.sh',config['deploy']['sut_worker'],config['deploy']['benchmark_worker'],'1',cpus[0]])
    subprocess.call(['./wait_to_be_running.sh',str(2)])
    fortio_ip ='' 
    nodejs_ip =''
    with open("live_config.yaml") as live_config:
        live_config = yaml.safe_load(live_config)
        fortio_ip = live_config["deploy"]["fortio_ip"] 
        nodejs_ip = live_config["deploy"]["service_ip"]
    print('--------------------------------------------------\n')
    print('------------------ Start Measurement -------------\n')

    result = []

    for i in range(1,max_pod+1):
        pod = i
        cpu = cpus[i-1]
        measurement = {'pod':pod,'cpu':cpu,'values':[]}
        print('------- MEASUREMENT - POD: {0} - CPU/POD: {1}'.format(str(pod),cpu))
        print('        ------- Update Deployment ------')
        #update deployment and wait until it gets ready
        subprocess.call(['./update_nodejs_app.sh',str(pod),cpu])
        subprocess.call(['./wait_to_be_running.sh',str(pod+1)])
        #time.sleep(60)
        lost_requests_percentage = 0
        qps = start_qps
        loop=0
        while loop < max_benchmark_iteration:
            loop+=1
            print('        ------- Benchmark - qps: {0} ------'.format(qps))
            # TODO call benchmark script
            start_time = time.time() 
            try:
               res = json.loads((requests.get(url="http://{0}:8080/fortio/?labels=Fortio&url=http://172.16.0.7:30044&qps={2}&t={3}s&n=&c=4&p=50, 75, 90, 99, 99.9&r=0.0001&H=Host: nodejsapp&H=User-Agent: fortio.org/fortio-1.3.2-pre&H=&H=&H=&runner=http&resolve=&grpc-ping-delay=0&json=on&save=on&load=Start&timeout=10s".format(fortio_ip,nodejs_ip,qps,benchmark_time))).text)
            except Exception as e:
               str(e)
               measurement['values'].append({'qps':qps,'avg_cpu':'N/A','req_lost':'N/A','avg_mem':'N/A','cpu_values':[],'mem_values':[]})
               lost_request_percentage = 0
            else:
               end_time = time.time()
               actual_qps = float(res["ActualQPS"])
               requested_qps = float(res["RequestedQPS"])
               lost_requests_percentage = (1 - (actual_qps/requested_qps))*100
               print(lost_requests_percentage)
               print(start_time)
               print(end_time)
               try:
                  # TODO collect CPU, MEM, Network info from prometheus
                  cpu_usage = json.loads(requests.get(url="http://10.106.36.184:9090/api/v1/query_range?query=sum(rate(container_cpu_usage_seconds_total{{container_name=\"nodejs-app\"}}[{3}s]))&start={0}&end={1}&step={2}".format(start_time,end_time,1,10)).text)
                  mem_usage = json.loads(requests.get(url="http://10.106.36.184:9090/api/v1/query_range?query=sum(rate(container_memory_usage_bytes{{container_name=\"nodejs-app\"}}[10s]))&start={0}&end={1}&step={2}".format(start_time,end_time,1,benchmark_time)).text)
                  #calculate cpu usage
               except Exception as e:
                  str(e)
                  measurement['values'].append({'qps':qps,'avg_cpu':'N/A','req_lost':lost_request_percentage,'avg_mem':'N/A','cpu_values':[],'mem_values':[]})
               else:
                  avg = []
                  cpu_values = cpu_usage['data']['result'][0]['values']
                  for value in cpu_values:
                     avg.append(float(value[1]))
                  cpu_avg = numpy.average(avg)
                  print("CPU usage: {0}".format(str(cpu_avg)))
                  #calculate mem usage
                  avg = []
                  mem_values = mem_usage['data']['result'][0]['values']
                  for value in mem_values:
                     avg.append(float(value[1]))
                  mem_avg = numpy.average(avg)
                  print("MEM usage: {0}".format(str(mem_avg)))
                  #save measurement info
                  measurement['values'].append({'qps':qps,'avg_cpu':cpu_avg,'req_lost':lost_requests_percentage,'avg_mem':mem_avg,'cpu_values':cpu_values,'mem_values':mem_values})
                  # TODO calculate CPU usage, lost_requests_percentage
            qps += step
            time.sleep(benchmark_time)

            # TODO store resource info
            #result.append(measurement)
            # write results to file
        with open('{0}.json'.format('class_'+datetime.datetime.strftime(datetime.datetime.now(),'%y_%m_%d_%H_%M_%S')+'_'+str(pod)),'w') as file_result:
            json.dump(measurement,file_result)
    print('--------------------------------------------------\n')
    #write result to file
    #with open('{0}.json'.format(datetime.datetime.strftime(datetime.datetime.now(),'%y_%m_%d_%H_%M_%S')),'w') as file_result:
    #    json.dump(result,file_result)
    subprocess.call(['./delete.sh'])
    
