import numpy
import matplotlib.pyplot as plt
import statistics
import os
import time
import math

#TODO seed erteket is be kell allitani
numpy.random.seed(0)

#TODO waiting time

class Model:
    """
    Represents the model logic
    """

    def __init__(self,min_server=1, max_server=1,initial_server=1, T=1, arrival_rate=1, serving_rate=1,desiredCPU=0.5,timeOut=None,cont_start=None,timeFrame=60):
        """
        Basic setup of the model:

        Params:
            min_server (int): minimum number of servers
            max_server (int): maximum number of servers
            T (int): count of timeslots
            arrival_rate (float): mean value of the poisson arrival
            serving_rate (float): mean value of exponential serving rate
            desiredCPU (float): desired CPU for scaling ( 0 < desiredCPU < 1) 
            timeOut (int): defined in periods 
        """
        self.min_server = min_server
        self.max_server = max_server
        self.initial_server = initial_server
        self.T = T
        self.arrival_rate = arrival_rate
        self.serving_rate = serving_rate
        self.desiredCPU = desiredCPU
        self.timeOut=timeOut
        self.cont_start = cont_start
        self.timeFrame = timeFrame

        #init data arrays
        self.L = [0,0]
        self.Mu = [2,2]
        self.S = [self.initial_server,self.initial_server]
        self.La = [0,0]
        self.Served = [0,0]
        #self.calculate_Mu_t(1)
        #self.calculate_Served_t(1)

        self.waiting = [] #-> stores in every iteration the count of the waiting requests in an array (i. index means that array[] piece of request is waiting for i iteration)
        self.responseTimes = {} #-> stores in every iteration the count of finished requests group by period 
        self.waitingData = [] # stores the waiting arrays in every iteration
        self.responseTimesData = [] #stores the responseTimes data in every iteration

        self.avgRespTime = []
        #init time period -> I do not use this
        self.t = 2
    
    #Setters
    def set_min_server(self,min_server):
        self.min_server = min_server
    
    def set_max_server(self,max_server):
        self.max_server = max_server
    
    def set_init_server(self,init_server):
        self.initial_server = init_server
        self.S = [init_server,init_server]

    def set_T(self,T):
        self.T=T

    def set_arrival(self,arrival):
        self.arrival_rate=arrival

    def set_serving(self,serving):
        self.serving_rate=serving

    def set_cpu(self,cpu):
        self.desiredCPU = cpu

    #-------


    def calculate_L_t(self,t):
        served = self.L[t-1] - (self.Mu[t-1] * self.S[t-1])
        served = served if served >= 0 else 0
        served += self.La[t]

        ## need to decrease with the timeout rate..
        timeout = 0
        if not self.timeOut is None:
            # if timeOut is x, drop all request older than x+1 (if timeout is big, it is negligeable (elhanyagolható))
            #get requests in t - timeout -1 period, end subtract all served requests since that point, we need to subtract the result from the current state
            timedout_requests = self.L[t-self.timeOut-1] if t-self.timeOut-1 > 0 else self.L[0]
            for i in range(self.timeOut+1):
                mu = self.Mu[t-i-1] if (t-i-1) >= 0 else self.Mu[0]
                S = self.S[t-i-1] if (t-i-1) >= 0 else self.S[0]
                L = self.L[t-i-1] if (t-i-1) >= 0 else self.L[0]
                timedout_requests-= min(mu * S,L)
            timeout = timedout_requests
        #timeout = self.L[t-2] - self.Served[t-1] - self.Served[t]
        served -= timeout if timeout > 0 else 0
        
        self.L.append(served if served > 0 else 0)

    def calculate_Served_t(self,t):
        #self.Served.append(min(self.Mu[t-1] * self.S[t-1],self.L[t-1]))
        self.Served.append(min(self.calc_full_serving(t),self.L[t-1]))

    def calc_full_serving(self,t):
        # if pod start time does not count
        if self.cont_start is None or self.cont_start == 0:
            return self.Mu[t-1] * self.S[t-1]
        elif 0 < self.cont_start < 1:
            new_cont = 0 if (self.S[t-1] - self.S[t-2]) < 0 else self.S[t-1] - self.S[t-2]
            return (1-self.cont_start)*new_cont*self.Mu[t-1] + self.Mu[t-1]*min(self.S[t-1],self.S[t-2])
        else:
            mu = self.Mu[t-self.cont_start-1] if (t-self.cont_start-1) >= 0 else self.Mu[0]
            S = self.S[t-self.cont_start-1] if (t-self.cont_start-1) >= 0 else self.S[0]
            return S*mu

    def calculate_S_t(self,t):
        #S_t_temp = math.ceil( min(self.Mu[t-1] * self.S[t-1],self.L[t-1])/(self.serving_rate * self.desiredCPU) )
        S_t_temp = math.ceil( min(self.calc_full_serving(t),self.L[t-1])/(self.serving_rate * self.desiredCPU) )

        if self.min_server <= S_t_temp <= self.max_server:
            self.S.append(S_t_temp)
        elif self.min_server > S_t_temp:
            self.S.append(self.min_server)
        elif self.max_server < S_t_temp:
            self.S.append(self.max_server)
        
    def calculate_Mu_t(self,t):
        rates = []

        for server in range(0,self.S[t]):
            number_of_served_requests = 0
            time = 0
            time += numpy.random.exponential(scale = 1 / self.serving_rate)
            while time < 1:
                number_of_served_requests += 1
                time += numpy.random.exponential(scale = 1 / self.serving_rate)
            
            rates.append(number_of_served_requests)
        self.Mu.append( numpy.average(rates) )

    def calculate_Waiting_t(self,t):
        #subtract timedout requests
        if not self.timeOut is None:
            timeout = self.timeOut
            while timeout+1 <= len(self.waiting):
                self.waiting.pop()

        # subtract served from the waiting queue from the last index 
        i = len(self.waiting)-1
        served = self.Served[t]
        while served > 0 and i >=0 :
            finished = 0
            if served >= self.waiting[i]:
                served -= self.waiting[i]
                finished = self.waiting[i]
                self.waiting[i] = 0
            else:
                self.waiting[i] -= served
                finished = served
                served = 0
            
            # update finished requests count
            if self.responseTimes.get(i) is None:
                self.responseTimes.update({i:finished})
            else:
                self.responseTimes.update({i:self.responseTimes.get(i)+finished})

            i-=1
        #remove all 0 element from the end of the list
        i = len(self.waiting)-1
        while i>= 0 and self.waiting[i]== 0:
            self.waiting.pop()
            i-=1
        #add to waitingData
        self.waitingData.append(self.waiting.copy())
        self.responseTimesData.append(self.responseTimes.copy())

    def print_all(self,t):
        print("{3}: Servers: {0}, Requests Arrived: {1}, Served: {2}, L_t: {4}, Waiting: {5}, finished: {6}".format(self.S[t],self.La[t],self.Served[t],t,self.L[t],self.waiting,self.responseTimes))

    def run(self,visualize = False):
        #T period
        for t in range(2,self.T+2):
            #requests arrive
            self.La.append(numpy.random.poisson(self.arrival_rate))

            self.calculate_Served_t(t)

            #calulate L[t]
            self.calculate_L_t(t)

            

            #calculate S[t]
            self.calculate_S_t(t)
            #calculate Mu[t]
            self.calculate_Mu_t(t)

            #calc waiting
            self.calculate_Waiting_t(t)
            if visualize:
                self.print_all(t)

            #add shift waiting queue to right and add the newly arrived requests
            self.waiting.insert(0,self.La[t])
        
        #print response and waiting information
        if visualize:
            print(mymodel.waitingData)
            print(mymodel.responseTimesData)


class Visualizer:
    def basic_data(self, mymodel):
        fig, axs = plt.subplots(2,2)
        #Histogram for requests in the system
        axs[0][0].hist(mymodel.L)
        axs[0][0].set_title('Hist: Requests in the system')

        

        #plot for [request served in period 0..8 / time]
        #served_plot = plt.figure(2)
        for i in range(0,9):
            x = []
            for line in mymodel.responseTimesData:
                x.append( line.get(i) if not (line.get(i) is None) else 0)
            axs[0][1].plot(x)
        axs[0][1].set_title('Count of requests served by respTime')

        #pie for served requests based on how many periods take to serve
        data = []
        labels = []
        last = mymodel.responseTimesData[len(mymodel.responseTimesData)-1]
        for k,v in last.items():
            data.append(v)
            labels.append(k)
        axs[1][0].pie(data,labels=labels,autopct='%.2f')
        axs[1][0].set_title('Requests by respTime (%)')

        #count of served requests
        axs[1][1].plot(mymodel.Served)
        axs[1][1].set_title('count of served requests')

    def pod_count_resp_time(self, mymodel, firstPeriod=None, lastPeriod=None):
        respTimes = self.calc_resp_time(mymodel)
        #print(respTimes)
        #last = mymodel.responseTimesData[len(mymodel.responseTimesData)-1]
        #summa = 0
        #for k,v in last.items():
        #    summa += v
        #print(summa)
        #print(summa / 10000 / numpy.average(mymodel.S))
        servers = self.calc_pod_count(mymodel)
        response_times = respTimes

        x1,y1 = create_intervals_for_plot(servers,mymodel.timeFrame)

        x2,y2 = create_intervals_for_plot(response_times,mymodel.timeFrame)
        #print(x1)
        x1,y1 = cut_by_frame(x1,y1,firstPeriod,lastPeriod)
        x2,y2 = cut_by_frame(x2,y2,firstPeriod,lastPeriod)
            
        fig, ax1 = plt.subplots()
        
        
        ax1.plot(x1,y1,'b')
        ax1.set_xlabel('time (s), period: {0}s'.format(mymodel.timeFrame))
        # Make the y-axis label, ticks and tick labels match the line color.
        ax1.set_ylabel('Pod count', color='b')
        ax1.tick_params('y', colors='b')

        ax2 = ax1.twinx()
        ax2.semilogy(x2,y2,'r')
        ax2.set_ylabel('avg rep time', color='r')
        ax2.tick_params('y', colors='r')
        

        fig.tight_layout()
        plt.show()

    def plot_data(self, models, plot_type = 'pod_count', timeFrame=60, firstPeriod=None, lastPeriod=None):
        if plot_type == 'pod_count':
            fig, ax1 = plt.subplots()
            for model in models:
                model_data = self.calc_full_pod_count_data(model,firstPeriod,lastPeriod)
                ax1.plot(model_data[0],model_data[1],label='Period: {0}s'.format(model.timeFrame))
        
            ax1.set_xlabel('time (s)')
            # Make the y-axis label, ticks and tick labels match the line color.
            ax1.set_ylabel('Pod count', color='b')
            ax1.tick_params('y', colors='b')

            fig.tight_layout()
            ax1.legend(loc='upper right')
            plt.show()
        elif plot_type == 'resp_time':
            fig, ax1 = plt.subplots()
            for model in models:
                model_data = self.calc_full_resp_time_data(model,firstPeriod,lastPeriod)
                ax1.semilogy(model_data[0],model_data[1],label='Period: {0}s'.format(model.timeFrame))
        
            ax1.set_xlabel('time (s)')
            # Make the y-axis label, ticks and tick labels match the line color.
            ax1.set_ylabel('Response time (s)', color='b')
            ax1.tick_params('y', colors='b')
            ax1.legend(loc='upper right')
            fig.tight_layout()
            plt.show()
        
    def calc_full_pod_count_data(self,model, firstPeriod, lastPeriod):
        pods = self.calc_pod_count(model)
        x1,y1 = create_intervals_for_plot(pods,model.timeFrame)
        x1,y1 =cut_by_frame(x1,y1,firstPeriod,lastPeriod)
        return x1,y1

    def calc_full_resp_time_data(self,model, firstPeriod, lastPeriod):
        response_times = self.calc_resp_time(model)
        x2,y2 = create_intervals_for_plot(response_times, model.timeFrame)
        #print(x1)
        x2,y2 = cut_by_frame(x2,y2,firstPeriod,lastPeriod)
        return x2,y2

    def calc_pod_count(self,model):
        return model.S[2:]

    def calc_resp_time(self,mymodel):
        #count average resp time / period
        respTimes = []
        for i in range(0,len(mymodel.responseTimesData)):
            line = mymodel.responseTimesData[i]
            newLine = {}
            if i > 0:
                lastLine = mymodel.responseTimesData[i-1]
                for k,v in line.items():
                    if(not lastLine.get(k) is None):
                        newLine.update({k:v-lastLine.get(k)})
                    else:
                        newLine.update({k:v})
            else:
                newLine = line
            times = []
            weights = []
            for k,v in newLine.items():
                times.append( (k+1)*mymodel.timeFrame) #( 1/(mymodel.serving_rate/mymodel.timeFrame) )  )
                weights.append(v)
            if len(times) > 0 and len(weights) > 0 and numpy.sum(weights) > 0:
                respTimes.append(numpy.average(times,weights=weights))
            else:
                respTimes.append(0)
        return respTimes

 
def create_intervals_for_plot(data,timeFrame):
    y1 = []

    for i in data:
        y1.append(i)
        y1.append(i)

    x1 = []
    #0112233
    for i in range(len(y1)):
        x1.append(i/2 if i % 2 == 0 else i/2+0.5 ) 

    x1 = list(map(lambda x: x*timeFrame,x1))

    return x1,y1

def cut_by_frame(x,y,firstPeriod,lastPeriod):
    if not firstPeriod is None and not lastPeriod is None:
        i,j = 0,0
        for k,x1 in enumerate(x):
            if x1 >=firstPeriod and i==0:
                i=k
            if x1 >=lastPeriod and j<=lastPeriod:
                x = x[round(i):round(j)]
                y= y[round(i):round(j)]
                return x,y
            j=k
            
    return x,y

if __name__ == "__main__":
    rate = 8
    timeFrame = 15 # time of one period: [s]
    serv_rate = 2
    cpu = 0.75
    cont_start = 0.3 # timeFrame * cont_start sec
    T = 120
    mymodel = Model(1,20,1,120,rate*timeFrame,serv_rate*timeFrame,cpu,None,cont_start,timeFrame)
    #mymodel = Model(1,10,1,9,240,120,0.5)
    
    mymodel.run(visualize=True)

    visualizer = Visualizer()
    visualizer.basic_data(mymodel)
    visualizer.pod_count_resp_time(mymodel)
    

    