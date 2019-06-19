import numpy as np
import matplotlib.pyplot as plt
import json
import argparse


class TimeGenerator:
    def __init__(self, measurement_length, random_seed):
        self.measurement_length = measurement_length * 60  # minutes * 60 = seconds
        self.wait_times = []
        self.send_times = []
        self.serve_times = []
        self.name = "TimeGenerator"
        self.random_seed = random_seed
        self.random = np.random.RandomState(seed=random_seed)

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
        timeframe = 90
        last_time = self.send_times[len(self.send_times) - 1]
        counts = []
        for i in range(0, int(last_time), timeframe):
            cnt = 0
            for time in self.send_times:
                if i <= time < i+timeframe:
                    cnt += 1
            counts.append(cnt)
        mean = sum(counts) / len(counts)
        plt.hist(self.send_times, bins=int(last_time / timeframe), histtype='step', label="Load")
        plt.axhline(mean, color="r", label="Mean load")
        plt.ylabel('Request count / ' + str(timeframe) + ' sec')
        plt.xlabel('Time in seconds')
        plt.legend(loc=4)
        if to_file:
            plt.savefig(self.name + ".png")
        else:
            plt.show()

    def write_to_file(self, extra_metadata, filename=None, file_extension=".json"):
        if filename is None:
            filename = self.name
        log = {}
        metadata = extra_metadata
        data = {}

        metadata["measurement_length"] = int(self.measurement_length / 60)
        metadata["random_seed"] = self.random_seed

        data["load_send_times"] = self.send_times
        data["load_wait_times"] = self.wait_times
        data["serve_times"] = self.serve_times

        log["metadata"] = metadata
        log["data"] = data

        with open(filename + file_extension, "w") as file:
            json.dump(log, file)
        return filename + file_extension


class PoissonTimeGenerator(TimeGenerator):
    def __init__(self, measurement_length, load_rate, serve_rate, random_seed=0):
        super().__init__(measurement_length, random_seed)
        self.load_rate = load_rate
        self.serve_rate = serve_rate
        self.name = "poisson_generated_times_length_" + str(int(self.measurement_length / 60)) + \
                    "min_load_rate_" + str(self.load_rate) + \
                    "_serve_rate_" + str(self.serve_rate) + \
                    "_random_seed_" + str(self.random_seed)
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
        metadata = {}
        metadata["load_rate"] = self.load_rate
        metadata["serve_rate"] = self.serve_rate
        metadata["type"] = "poisson"
        return self.write_to_file(metadata, filename, file_extension)


class MMPPTimeGenerator(TimeGenerator):
    def __init__(self, measurement_length, load_rate_list, transition_matrix, serve_rate, random_seed=0):
        super().__init__(measurement_length, random_seed)
        self.load_rate_list = load_rate_list
        self.serve_rate = serve_rate
        load_rate_list_string = ""
        for r in load_rate_list:
            load_rate_list_string += str(r) + "_"
        self.load_rate_list_string = load_rate_list_string[:-1]
        self.name = "mmpp_generated_times_length_" + str(int(self.measurement_length / 60)) + \
                    "min_load_rate_" + str(self.load_rate_list_string) + \
                    "_serve_rate_" + str(self.serve_rate) + \
                    "_random_seed_" + str(self.random_seed)
        # self.transition_matrix = [[0.99, 0.006, 0.002, 0.002],
        #                           [0.005, 0.99, 0.005, 0.0],
        #                           [0.0, 0.005, 0.99, 0.005],
        #                           [0.0, 0.0, 0.01, 0.99]]
        # self.transition_matrix = [[0.5, 0.5],
        #                           [0.5, 0.5]]
        matrix_n = len(load_rate_list)
        self.transition_matrix = np.array(transition_matrix).reshape((matrix_n, matrix_n)).tolist()
        self.current_state = 0
        self.__calculate_times()

    def __next_state(self):
        random = self.random.random_sample()
        i = 0
        for state in range(0, len(self.transition_matrix[self.current_state])):
            i += self.transition_matrix[self.current_state][state]
            # print(str(random) + "   " + str(i))
            if random < i:
                return state

    def __calculate_times(self):
        self.wait_times = []
        self.send_times = [0]
        sum_wait_time = 0
        state_change_time = 0
        while sum_wait_time < self.measurement_length:
            wait_time = self.random.exponential(1 / self.load_rate_list[self.current_state])
            sum_wait_time += wait_time
            self.wait_times.append(wait_time)
            self.send_times.append(sum_wait_time)
            if state_change_time <= sum_wait_time - 90:
                state_change_time = sum_wait_time
                self.current_state = self.__next_state()
        self.serve_times = []
        for i in range(0, len(self.send_times)):
            self.serve_times.append(self.random.exponential(1 / self.serve_rate))

    def write_times_to_file(self, filename=None, file_extension=".json"):
        metadata = {}
        metadata["load_rate"] = self.load_rate_list_string
        metadata["transition_matrix"] = self.transition_matrix
        metadata["serve_rate"] = self.serve_rate
        metadata["type"] = "mmpp"
        return self.write_to_file(metadata, filename, file_extension)


def load_times_from_file(filename):
    with open(filename, "r") as file:
        log = json.load(file)
    if log is None:
        raise FileNotFoundError
    return log["data"]["load_send_times"], log["data"]["load_wait_times"], log["data"]["serve_times"], log["metadata"]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--length", help="Length of the measurement [min]", type=int)
    parser.add_argument("--type", help="Poisson or MMPP load generation [poisson/mmpp]")
    parser.add_argument("--load-rate", help="Rate for Poisson load time generation", type=int)
    parser.add_argument('--load-rate-list', help="List of rates for MMPP load time generation", nargs='+', type=int)
    parser.add_argument('--trans-matrix', help="Transition matrix for MMPP load time generation", nargs='+', type=float)
    parser.add_argument("--serve-rate", help="Rate for serve time generation", type=int)
    parser.add_argument("--random-seed", help="Random seed of generation", type=int, default=None)
    args = parser.parse_args()

    if args.type == "poisson":
        if args.random_seed is not None:
            tg = PoissonTimeGenerator(args.length, args.load_rate, args.serve_rate, args.random_seed)
        else:
            tg = PoissonTimeGenerator(args.length, args.load_rate, args.serve_rate)
    else:
        if args.random_seed is not None:
            tg = MMPPTimeGenerator(args.length, args.load_rate_list, args.trans_matrix, args.serve_rate, args.random_seed)
        else:
            tg = MMPPTimeGenerator(args.length, args.load_rate_list, args.serve_rate)
    file_name = tg.write_times_to_file()
    tg.plot_send_times(True)
    print(file_name)

    # load_send_times, load_wait_times, serve_times, metadata = load_times_from_file(file_name)
    # print(load_send_times)
    # print(load_wait_times)
    # print(serve_times)
    # print(metadata)
