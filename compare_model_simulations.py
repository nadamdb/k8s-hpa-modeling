import math

from continuous_model.autoscale_predictor import MMcAnalysisBasedAutoscalePredictor
from discrete_model.mymodel import Model
import generator.timegenerator as load_gen


if __name__ == "__main__":
    # Load parameters
    simulation_length_minutes = 10 # [min]
    arrival_rate = 12  # [request/s]
    service_rate = 2 # [request/s]
    base_file_name = "experiment_length-{length}min_load-rate-{load}_serve-rate-{serve}".format(length=simulation_length_minutes,
                                                                                                       load=arrival_rate,
                                                                                                        serve=service_rate)
    load_file_name = base_file_name + ".load"

    # autoscaling parameters
    scale_time_frame = 10 # [s]
    desired_cpu = 0.75
    initial_server_cnt = 5

    # TO BE ALIGNED PARAMETERS (cont)
    scaling_tolerance = 0.05

    # TO BE ALIGNED PARAMETERS (disc)
    min_server = 1
    max_server = 100000000000
    number_of_time_frames = math.ceil(simulation_length_minutes * 60 / scale_time_frame)
    cont_start = 0

    # generate load, write to file and read it back to give it to the models
    filename = load_gen.write_times_to_file(simulation_length_minutes, arrival_rate, service_rate, name=load_file_name)
    load_send_times, load_wait_times, serve_times, metadata = load_gen.load_times_from_file(filename)

    # instantiate and run the continuous model
    continuous_model = MMcAnalysisBasedAutoscalePredictor(initial_server_cnt, arrival_rate, service_rate, scale_time_frame,
                                                          desired_cpu, scaling_tolerance)
    continuous_model.write_pod_cnt_to_file(load_send_times, file_name=base_file_name + ".continuous.out")

    # instantiate and run the discrete model
    discrete_model = Model(min_server, max_server, initial_server_cnt, T=number_of_time_frames,
                           arrival_rate=arrival_rate * scale_time_frame, serving_rate=service_rate * scale_time_frame,
                           desiredCPU=desired_cpu, cont_start=cont_start,
                           mode=Model.READ_LOAD, already_read_load=(load_send_times, load_wait_times, serve_times, metadata))
    discrete_model.run()
    discrete_model.write_to_file(base_file_name + ".discrete.out")


