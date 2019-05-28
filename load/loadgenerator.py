import numpy as np
import matplotlib.pyplot as plt
import csv


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

    def write_times_to_csv(self):
        with open(self.name + ".csv", mode='w') as wait_times_file:
            wait_times_writer = csv.writer(wait_times_file, delimiter=',')
            wait_times_writer.writerow(self.wait_times)
            wait_times_writer.writerow(self.send_times)

    def plot_send_times(self, to_file=False):
        last_time = self.send_times[len(self.send_times) - 1]
        plt.hist(self.send_times, bins=int(last_time / 15))
        plt.ylabel('Request count')
        plt.xlabel('Time in seconds')
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


if __name__ == '__main__':
    test = PoissonLoadGenerator(12, 60)
    test.write_times_to_csv()
    test.plot_send_times(True)
