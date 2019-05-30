from continuous_model.autoscale_predictor import MMcAnalysisBasedAutoscalePredictor
from generator.timegenerator import PoissonLoadGenerator
import json

if __name__ == "__main__":
    initial_pod_cnt = 5
    arrival_rate = 1.0
    service_rate = 0.01
    scale_time_frame = 2.0
    desired_cpu = 0.75
    scaling_tolerance = 0.3

    load_gen = PoissonLoadGenerator(rate=arrival_rate, measurement_length=1)
    autoscale_pred = MMcAnalysisBasedAutoscalePredictor(initial_pod_cnt, arrival_rate, service_rate, scale_time_frame, desired_cpu,
                                                        scaling_tolerance)

    # TODO: tweak parameters to enforce scaling...
    measurement_dict = {"data": [], "time": []}
    for arrival_time_stamp in load_gen.get_send_times():
        autoscale_pred.get_current_pod_count_set_cpu_pred(arrival_time_stamp)
        measurement_dict["data"].append(autoscale_pred.current_pod_count)
        measurement_dict["time"].append(arrival_time_stamp)

    with open("test.json", "w") as file:
        json.dump(measurement_dict, file)

