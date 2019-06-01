import numpy as np
import matplotlib.pyplot as plt
import json
import argparse


class TimeGenerator:
    def __init__(self, measurement_length):
        self.measurement_length = measurement_length * 60  # minutes * 60 = seconds
        self.wait_times = []
        self.send_times = []
        self.serve_times = []
        self.name = "TimeGenerator"

    def __calculate_times(self):
        raise NotImplementedError

    def get_wait_times(self):
        return self.wait_times

    def get_send_times(self):
        return self.send_times

    def get_serve_times(self):
        return self.send_times

    def get_all_times(self):
        return self.send_times, self.wait_times, self.serve_times

    def plot_send_times(self, to_file=False):
        last_time = self.send_times[len(self.send_times) - 1]
        counts = []
        for i in range(0, int(last_time), 15):
            cnt = 0
            for time in self.send_times:
                if i <= time < i+15:
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


class PoissonTimeGenerator(TimeGenerator):
    def __init__(self, measurement_length, load_rate, serve_rate, random_seed=0):
        super().__init__(measurement_length)
        self.load_rate = load_rate
        self.serve_rate = serve_rate
        self.random_seed = random_seed
        self.name = "poisson_generated_times_length_" + str(int(self.measurement_length / 60)) + \
                    "min_load_rate_" + str(self.load_rate) + \
                    "_serve_rate_" + str(self.serve_rate) + \
                    "_random_seed_" + str(self.random_seed)
        self.random = np.random.RandomState(seed=random_seed)
        self.__calculate_times()

    def __calculate_times(self):
        self.wait_times = []
        self.send_times = [0]
        sum_wait_time = 0
        while sum_wait_time < self.measurement_length:
            wait_time = self.random.exponential(1 / self.load_rate)
            sum_wait_time += wait_time
            self.wait_times.append(wait_time)
            self.send_times.append(sum_wait_time)
        self.serve_times = []
        for i in range(0, len(self.send_times)):
            self.serve_times.append(self.random.exponential(1 / self.serve_rate))

    def write_times_to_file(self, filename=None, file_extension=".json"):
        if filename is None:
            filename = self.name
        log = {}
        metadata = {}
        data = {}

        metadata["measurements_length"] = self.measurement_length
        metadata["load_rate"] = self.load_rate
        metadata["serve_rate"] = self.serve_rate
        metadata["random_seed"] = self.random_seed

        data["load_send_times"] = self.send_times
        data["load_wait_times"] = self.wait_times
        data["serve_times"] = self.serve_times

        log["metadata"] = metadata
        log["data"] = data

        with open(filename + file_extension, "w") as file:
            json.dump(log, file)
        return filename + file_extension


def load_times_from_file(filename):
    with open(filename, "r") as file:
        log = json.load(file)
    if log is None:
        raise FileNotFoundError
    return log["data"]["load_send_times"], log["data"]["load_wait_times"], log["data"]["serve_times"], log["metadata"]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--length", help="Length of the measurement [min]", type=int)
    parser.add_argument("--load-rate", help="Rate for load time generation", type=int)
    parser.add_argument("--serve-rate", help="Rate for serve time generation", type=int)
    parser.add_argument("--random-seed", help="Random seed of generation", type=int, default=None)
    args = parser.parse_args()

    if args.random_seed is not None:
        ptg = PoissonTimeGenerator(args.length, args.load_rate, args.serve_rate, args.random_seed)
    else:
        ptg = PoissonTimeGenerator(args.length, args.load_rate, args.serve_rate)
    file_name = ptg.write_times_to_file()
    print(file_name)
    # load_send_times, load_wait_times, serve_times, metadata = load_times_from_file(file_name)
    # print(load_send_times)
    # print(load_wait_times)
    # print(serve_times)
    # print(metadata)
