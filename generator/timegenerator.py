import numpy as np
import matplotlib.pyplot as plt
import json


class LoadGenerator:
    def __init__(self, measurement_length):
        self.measurement_length = measurement_length * 60  # minutes * 60 = seconds
        self.wait_times = []
        self.send_times = []
        self.name = "LoadGenerator"

    def __calculate_times(self):
        raise NotImplementedError

    def get_wait_times(self):
        return self.wait_times

    def get_send_times(self):
        return self.send_times

    def plot_send_times(self, to_file=False):
        last_time = self.send_times[len(self.send_times) - 1]
        #plt.hist(self.send_times, bins=int(last_time / 1))
        counts = []
        for i in range(0, int(last_time), 15):
            cnt = 0
            for time in self.send_times:
                if time >= i and time < i+15:
                    cnt += 1
            counts.append(cnt)
        mean = sum(counts) / len(counts)
        plt.hist(self.send_times, bins=int(last_time / 15), histtype='step', label="Load")
        plt.axhline(mean, color="r", label="Mean load")
        plt.ylabel('Request count / 15 sec')
        plt.xlabel('Time in seconds')
        plt.legend(loc=4)
        if to_file:
            plt.savefig(self.name + ".png")
        else:
            plt.show()


class PoissonLoadGenerator(LoadGenerator):
    def __init__(self, rate, measurement_length):
        super().__init__(measurement_length)
        self.rate = rate
        self.name = "poisson_times_rate_" + str(self.rate) + "_length_" + str(measurement_length) + "_min"
        self.__calculate_times()

    def __calculate_times(self):
        self.wait_times = []
        self.send_times = [0]
        sum_wait_time = 0
        while sum_wait_time < self.measurement_length:
            wait_time = np.random.exponential(1 / self.rate)
            sum_wait_time += wait_time
            self.wait_times.append(wait_time)
            self.send_times.append(sum_wait_time)


def generate_serve_times(num_of_reqs, rate):
    serve_times = []
    for i in range(0, num_of_reqs):
        serve_times.append(np.random.exponential(1/rate))
    return serve_times


def write_times_to_file(length, load_rate, serve_rate):
    load_generator = PoissonLoadGenerator(load_rate, length)
    load_send_times = load_generator.get_send_times()
    load_wait_times = load_generator.get_wait_times()

    serve_times = generate_serve_times(len(load_send_times), serve_rate)

    name = "generated_times_length_" + str(length) + "min_load_rate_" + str(load_rate) + "_serve_rate_" + str(serve_rate)

    log = {}
    metadata = {}
    data = {}

    metadata["measurements_length"] = length
    metadata["load_rate"] = load_rate
    metadata["serve_rate"] = serve_rate

    data["load_send_times"] = load_send_times
    data["load_wait_times"] = load_wait_times
    data["serve_times"] = serve_times

    log["metadata"] = metadata
    log["data"] = data

    with open(name + ".json", "w") as file:
        json.dump(log, file)
    return name + ".json"


def load_times_from_file(filename):
    log = {}
    with open(filename, "r") as file:
        log = json.load(file)
    if log == {}:
        raise FileNotFoundError
    return log["data"]["load_send_times"], log["data"]["load_wait_times"], log["data"]["serve_times"], log["metadata"]

if __name__ == '__main__':
    #test = PoissonLoadGenerator(5, 1)
    #test.plot_send_times(True)

    # Pelda a hasznalatra
    filename = write_times_to_file(60, 12, 2)
    load_send_times, load_wait_times, serve_times, metadata = load_times_from_file(filename)
    print(load_send_times)
    print(load_wait_times)
    print(serve_times)
    print(metadata)
