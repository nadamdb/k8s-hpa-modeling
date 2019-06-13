import math
import json
import random


from .new_single_slope import NewSingleSlopeAnalyzer


class AutoscalePredictor(object):

    def __init__(self, initial_pod_cnt, arrival_rate, pod_service_rate, time_frame, desired_cpu, scaling_tolerance,
                 min_pod_count=None, max_pod_count=None, downscale_stabilization_time=0):
        """
        Interface for autoscaling predictors. Provides a basic autoscaling model, which uses the same amount of infromation as the a more
        sophisticated model but using only the "load paramter" (= self.arrival_rate / self.pod_service_rate / self.current_pod_count) of
        an MMc system which is used as a static CPU utilization prediction.

        :param initial_pod_cnt:
        :param arrival_rate:
        :param pod_service_rate:
        :param time_frame: time interval to check scaling decision
        :param desired_cpu: CPU utilization which the autoscaler tries to maintain
        :param scaling_tolerance: No scaling decision shall be made if between desired_cpu +/- scaling_tolerance
        :param max_pod_count:
        :param min_pod_count:
        """
        self.desired_cpu = desired_cpu
        self.scaling_tolerance = scaling_tolerance
        self.time_frame = time_frame
        self.current_time = 0.0
        self.last_downscale_time = 0.0
        self.current_pod_count = self.prev_pod_count = initial_pod_cnt
        self.arrival_rate = arrival_rate
        self.pod_service_rate = pod_service_rate
        self.current_cpu_prediction = 0.0
        self.downscale_stabilization_time = downscale_stabilization_time
        if min_pod_count is None:
            self.min_pod_count = 1
        else:
            self.min_pod_count = min_pod_count
        if max_pod_count is None:
            self.max_pod_count = float('inf')
        else:
            self.max_pod_count = max_pod_count

    def set_new_current_pod_count(self):
        """
        The new number of pods must be calculated according to k8s rule, but based on the
        predicted cpu usage instead of the measured one.

        :param self.current_cpu_prediction:
        :return:
        """
        self.prev_pod_count = self.current_pod_count
        scaling_ratio = self.current_cpu_prediction / self.desired_cpu
        if math.fabs(scaling_ratio - 1.0) > self.scaling_tolerance:
            # scaling needs to be done, BUT not above max pod_count
            tmp_current_pod_count = max(self.min_pod_count,
                                         min(math.ceil(self.current_pod_count * scaling_ratio),
                                             self.max_pod_count))
            # if we are downscaling, we have to check if we are over the downscale stabilization time
            if tmp_current_pod_count >= self.prev_pod_count or \
                    self.last_downscale_time + self.downscale_stabilization_time <= self.current_time:
                self.current_pod_count = tmp_current_pod_count
        # If we are scaling down, update the according variable
        if self.current_pod_count < self.prev_pod_count:
            self.last_downscale_time = self.current_time

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


class MMcAnalysisBasedAutoscalePredictor(AutoscalePredictor):

    def __init__(self, initial_pod_cnt, arrival_rate, pod_service_rate, time_frame, desired_cpu, scaling_tolerance,
                 min_pod_count=None, max_pod_count=None, downscale_stabilization_time=0):
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
        super().__init__(initial_pod_cnt, arrival_rate, pod_service_rate, time_frame, desired_cpu, scaling_tolerance,
                         min_pod_count, max_pod_count, downscale_stabilization_time)
        self.mmc_analyzer = self.get_mmc_analyzer_instance()
        self.queue_length_cpu_pred_compensation = 0.0

    def get_mmc_analyzer_instance(self):
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
            # set it based on the previous estimation on the CPU, the value must be bounded by the current maximal number of active pod
            # count
            # NOTE: in case of a BIG upscale jump, we assume even all of the new pods can be immediately at work.
            # We don't allow having 0 initial active pods
            initial_active_pod = max(self.min_pod_count,
                                     min(math.ceil(self.current_cpu_prediction * self.prev_pod_count),
                                         self.current_pod_count))
            # initial_active_pod = random.choice(range(self.min_pod_count, self.current_pod_count + 1))
        if self.mmc_analyzer is None:
            # in our analytical approach in case of unstable M/M/c, the cpu usage converges to 1.0
            # It is also possible to use the load parameter to better estimate the next pod count
            # TODO: other options based on k8s autoscaling algorithm???
            # prediction = self.arrival_rate / self.pod_service_rate / self.current_pod_count       # mmcload
            prediction = 1.0              # 1
            # prediction = self.arrival_rate / self.pod_service_rate    # Lambdapermu

            # remember the compensation of CPU utilization of queued requests
            self.queue_length_cpu_pred_compensation = (self.arrival_rate - self.current_pod_count * self.pod_service_rate) / \
                                                       self.pod_service_rate
            print("Unstable M/M/c CPU usage estimation was used, total CPU usage compensation: {}".
                  format(self.queue_length_cpu_pred_compensation))
        else:
            sum_func_etha_0 = self.mmc_analyzer.get_sum_of_first_derivates(self.mmc_analyzer.func_etha, initial_active_pod, 0)
            sum_func_delta_c_0 = self.mmc_analyzer.get_sum_of_first_derivates(self.mmc_analyzer.func_delta_c, initial_active_pod, 0)

            # with solution pair index given, there should be only a single element in the result lists
            expected_sum_T0 = -1.0 * sum_func_etha_0[0]
            expected_sum_weighted_busy_time = -1.0 * sum_func_delta_c_0[0]

            prediction = expected_sum_weighted_busy_time / expected_sum_T0 / self.current_pod_count
            print("Clever M/M/c based CPU usage prediction was used: {}".format(prediction))
            # compensate the utilization with the utilization of the queued requests
            cpu_usage_room_left = 1.0 - prediction
            prediction += min(cpu_usage_room_left, self.queue_length_cpu_pred_compensation)
            # either we used all compensation, or there is some left for the next scaling event
            self.queue_length_cpu_pred_compensation = max(0.0, self.queue_length_cpu_pred_compensation - cpu_usage_room_left)
            print("Queue length compensated CPU usage prediction: {}".format(prediction))
        self.current_cpu_prediction = prediction
        return prediction

    def set_new_current_pod_count(self):
        """
        Creates a new MMC analyzer if needed.

        :return:
        """
        super().set_new_current_pod_count()
        if self.current_pod_count != self.prev_pod_count:
            self.mmc_analyzer = self.get_mmc_analyzer_instance()

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


class AdaptiveRateEstimatingMMcBasedAutoscalePredictor(MMcAnalysisBasedAutoscalePredictor):

    def __init__(self, initial_pod_cnt, arrival_rate, pod_service_rate, time_frame, desired_cpu, scaling_tolerance,
                 min_pod_count=None, max_pod_count=None, downscale_stabilization_time=0):
        """
        During simulation reactively changes the arrival and pod service rates according to the recent concrete arrival and service times.

        :param initial_pod_cnt:
        :param arrival_rate: Basically ignored, it is estimated from input in every timeframe
        :param pod_service_rate: Basically ignored, it is estimated from input in every timeframe
        :param time_frame:
        :param desired_cpu:
        :param scaling_tolerance:
        :param min_pod_count:
        :param max_pod_count:
        """
        super().__init__(initial_pod_cnt, arrival_rate, pod_service_rate, time_frame, desired_cpu, scaling_tolerance,
                         min_pod_count, max_pod_count, downscale_stabilization_time)
        # calling self.get_mmc_analyzer_instance() is not needed, called in the base constructor

    def write_pod_cnt_to_file_adaptive(self, arrival_time_stamps, service_times, file_name):
        """

        :param arrival_time_stamps:
        :param service_times:
        :param file_name:
        :return:
        """
        sum_of_inter_arrival_times = 0.0
        arrival_count = 0
        sum_of_service_times = 0.0
        pod_count_predictions = {"time": [], "data": []}
        previous_current_time = self.current_time

        for current_time, service_time in zip(arrival_time_stamps, service_times):
            if current_time > self.current_time + self.time_frame \
                    and sum_of_service_times > 0 and sum_of_inter_arrival_times > 0 and arrival_count > 0:
                # estimated arrival rate is the reciprocal of the expected value
                self.arrival_rate = arrival_count / sum_of_inter_arrival_times
                self.pod_service_rate = arrival_count / sum_of_service_times
                self.mmc_analyzer = self.get_mmc_analyzer_instance()
                # in every scaling period, reset the empirical rates
                sum_of_inter_arrival_times = 0.0
                arrival_count = 0
                sum_of_service_times = 0.0
            self.get_current_pod_count_set_cpu_pred(current_time)
            sum_of_inter_arrival_times += current_time - previous_current_time
            sum_of_service_times += service_time
            arrival_count += 1
            previous_current_time = current_time
            pod_count_predictions["data"].append(self.current_pod_count)
            pod_count_predictions["time"].append(current_time)

        with open(file_name, "w") as file:
            json.dump(pod_count_predictions, file)


if __name__ == '__main__':

    test = MMcAnalysisBasedAutoscalePredictor(5, 10, 1.0, time_frame=15.0, desired_cpu=0.75, scaling_tolerance=0.01)
    for t in range(0, 650, 5):
        print("{t},{p},{c}".format(p=test.get_current_pod_count_set_cpu_pred(t), t=t, c=test.current_cpu_prediction))
