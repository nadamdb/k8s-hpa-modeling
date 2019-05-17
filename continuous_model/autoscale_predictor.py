from new_single_slope import NewSingleSlopeAnalyzer
import math


class AutoscalePredictor(object):

    def __init__(self, initial_pod_cnt, arrival_rate, pod_service_rate, time_frame, desired_cpu, scaling_tolerance):
        """
        Predicts the Kubernetes autoscaling in reaction to the incoming load.

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
        # seemingly only solution_pair_index==0 produces valid results.
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

        :param initial_active_pod: if not given, current_pod_count / 2 is used.
        :return:
        """
        if initial_active_pod is None:
            initial_active_pod = int(self.current_pod_count / 2)
        if self.mmc_analyzer is None:
            # in our analytical approach in case of unstable M/M/c, the cpu usage converges to 1.0
            return 1.0
        else:
            sum_func_etha_0 = self.mmc_analyzer.get_sum_of_first_derivates(self.mmc_analyzer.func_etha, initial_active_pod, 0)
            sum_func_delta_c_0 = self.mmc_analyzer.get_sum_of_first_derivates(self.mmc_analyzer.func_delta_c, initial_active_pod, 0)

            # with solution pair index given, there should be only a single element in the result lists
            expected_sum_T0 = -1.0 * sum_func_etha_0[0]
            expected_sum_weighted_busy_time = -1.0 * sum_func_delta_c_0[0]

            return expected_sum_weighted_busy_time / expected_sum_T0

    def get_current_pod_count(self, current_time):
        """
        Performs scaling if necessary according to the configuration of time frame and the prediction results.

        :param current_time:
        :return:
        """
        if current_time >= self.current_time + self.time_frame:
            self.current_time = current_time
            cpu_usage_prediction = self.predict_cpu_usage()
            if cpu_usage_prediction > self.desired_cpu + self.scaling_tolerance or \
                cpu_usage_prediction < self.desired_cpu - self.scaling_tolerance:
                # scaling needs to be done, and the new number of pods must be calculated according to k8s rule, but based on the
                # predicted cpu usage instead of the measured one.
                self.current_pod_count = math.ceil(self.current_pod_count * cpu_usage_prediction / self.desired_cpu)
                self.mmc_analyzer = self.instantiate_mmc_analyzer()
        return self.current_pod_count


if __name__ == '__main__':

    test = AutoscalePredictor(5, 10, 1.0, time_frame=5.0, desired_cpu=0.75, scaling_tolerance=0.03)
    for t in range(0, 650, 5):
        print("{t},{p}".format(p=test.get_current_pod_count(t), t=t))
