import math
import json


from .new_single_slope import NewSingleSlopeAnalyzer


class AutoscalePredictor(object):

    def __init__(self, initial_pod_cnt, arrival_rate, pod_service_rate, time_frame, desired_cpu, scaling_tolerance):
        """
        Interface for autoscaling predictors.

        :param initial_pod_cnt:
        :param arrival_rate:
        :param pod_service_rate:
        :param time_frame: time interval to check scaling decision
        :param desired_cpu: CPU utilization which the autoscaler tries to maintain
        :param scaling_tolerance: No scaling decision shall be made if between desired_cpu +/- scaling_tolerance
        """
        self.desired_cpu = desired_cpu
        self.scaling_tolerance = scaling_tolerance
        self.time_frame = time_frame
        self.current_time = 0.0
        self.current_pod_count = initial_pod_cnt
        self.arrival_rate = arrival_rate
        self.pod_service_rate = pod_service_rate
        self.current_cpu_prediction = 0.0

    def set_new_current_pod_count(self):
        """
        The new number of pods must be calculated according to k8s rule, but based on the
        predicted cpu usage instead of the measured one.

        :param self.current_cpu_prediction:
        :return:
        """
        if self.current_cpu_prediction > self.desired_cpu + self.scaling_tolerance or \
                self.current_cpu_prediction < self.desired_cpu - self.scaling_tolerance:
            # scaling needs to be done, and
            self.current_pod_count = math.ceil(self.current_pod_count * self.current_cpu_prediction / self.desired_cpu)

    def get_current_pod_count_set_cpu_pred(self, current_time):
        """
        Baseline pod count prediction on lamda / c / mu. Must ste the self.current_cpu_prediction to the newest value.

        :param current_time:
        :return:
        """
        if current_time >= self.current_time + self.time_frame:
            self.current_time = current_time
            self.current_cpu_prediction = self.arrival_rate / self.pod_service_rate / self.current_pod_count
            self.set_new_current_pod_count()
        return self.current_pod_count


class MMcAnalysisBasedAutoscalePredictor(AutoscalePredictor):

    def __init__(self, initial_pod_cnt, arrival_rate, pod_service_rate, time_frame, desired_cpu, scaling_tolerance):
        """
        Predicts the Kubernetes autoscaling in reaction to the incoming load.

        :param initial_pod_cnt:
        :param arrival_rate:
        :param pod_service_rate:
        :param time_frame:
        :param desired_cpu:
        :param scaling_tolerance:
        """
        # seemingly only solution_pair_index==0 produces valid results.
        super().__init__(initial_pod_cnt, arrival_rate, pod_service_rate, time_frame, desired_cpu, scaling_tolerance)
        self.mmc_analyzer = self.instantiate_mmc_analyzer()

    def instantiate_mmc_analyzer(self):
        """
        Creates the single slope M/M/c analyzer, respecting the current values of the model: arrival_rate, pod_service_rate AND most
        importantly current_pod_count.

        :return:
        """
        if self.arrival_rate >= self.current_pod_count * self.pod_service_rate:
            # The model is not able to predict CPU usage under these circumstances (it makes the M/M/c queue unstable).
            return None
        return NewSingleSlopeAnalyzer(lambda_=self.arrival_rate, mu_=self.pod_service_rate,
                                                   c=self.current_pod_count, solution_pair_index=0)

    def predict_cpu_usage(self, initial_active_pod=None):
        """
        Predicts CPU usage based on the ratio of the expected values of total weighted busy time of a single slope and the time spent
        until the M/M/c system becomes idle.

        :param initial_active_pod: Active pod count at the beginning of the CPU usage prediction interval if not given, current_pod_count /
                                   2 is used.
        :return:
        """
        prediction = None
        if initial_active_pod is None:
            initial_active_pod = int(self.current_pod_count / 2)
        if self.mmc_analyzer is None:
            # in our analytical approach in case of unstable M/M/c, the cpu usage converges to 1.0
            prediction = 1.0
            print("Unstable M/M/c CPU usage estimation was used")
        else:
            sum_func_etha_0 = self.mmc_analyzer.get_sum_of_first_derivates(self.mmc_analyzer.func_etha, initial_active_pod, 0)
            sum_func_delta_c_0 = self.mmc_analyzer.get_sum_of_first_derivates(self.mmc_analyzer.func_delta_c, initial_active_pod, 0)

            # with solution pair index given, there should be only a single element in the result lists
            expected_sum_T0 = -1.0 * sum_func_etha_0[0]
            expected_sum_weighted_busy_time = -1.0 * sum_func_delta_c_0[0]

            prediction = expected_sum_weighted_busy_time / expected_sum_T0 / self.current_pod_count
            print("Clever M/M/c based CPU usage prediction was used: {}".format(prediction))
        self.current_cpu_prediction = prediction
        return prediction

    def set_new_current_pod_count(self):
        """
        Creates a new MMC analyzer if needed.

        :return:
        """
        prev_current_pod = self.current_pod_count
        super().set_new_current_pod_count()
        if self.current_pod_count != prev_current_pod:
            self.mmc_analyzer = self.instantiate_mmc_analyzer()

    def get_current_pod_count_set_cpu_pred(self, current_time):
        """
        Performs scaling if necessary according to the configuration of time frame and the prediction results.

        :param current_time:
        :return:
        """
        if current_time >= self.current_time + self.time_frame:
            self.current_time = current_time
            self.current_cpu_prediction = self.predict_cpu_usage()
            self.set_new_current_pod_count()
        return self.current_pod_count

    def write_pod_cnt_to_file(self, arrival_time_stamps, file_name):
        """
        Writes pod count predictions to a file in format {"time": [], "data": []}

        :param arrival_time_stamps: iterable of arrival times
        :param file_name:
        :return:
        """
        pod_count_predictions = {"time": [], "data": []}
        for current_time in arrival_time_stamps:
            self.get_current_pod_count_set_cpu_pred(current_time)
            pod_count_predictions["data"].append(self.current_pod_count)
            pod_count_predictions["time"].append(current_time)

        with open(file_name, "w") as file:
            json.dump(pod_count_predictions, file)


if __name__ == '__main__':

    test = MMcAnalysisBasedAutoscalePredictor(5, 10, 1.0, time_frame=15.0, desired_cpu=0.75, scaling_tolerance=0.01)
    for t in range(0, 650, 5):
        print("{t},{p},{c}".format(p=test.get_current_pod_count_set_cpu_pred(t), t=t, c=test.current_cpu_prediction))
