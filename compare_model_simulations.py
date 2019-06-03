import math

from continuous_model.autoscale_predictor import MMcAnalysisBasedAutoscalePredictor, AutoscalePredictor
from discrete_model.mymodel import Model
import generator.timegenerator as load_gen


if __name__ == "__main__":
    for arrival_rate in [4, 10, 20]:
        for service_rate in [2, 6, 10]:
            # Load parameters
            print("\nSIMULATION ROUND: arrival rate: {}, service rate: {}".format(arrival_rate, service_rate))
            simulation_length_minutes = 30 # [min]
            base_file_name = "model_comp_results/experiment_length-{length}min_load-rate-{load}_serve-rate-{serve}".format(
                                                    length=simulation_length_minutes, load=arrival_rate, serve=service_rate)
            load_file_name = base_file_name + ".load"

            # autoscaling parameters
            scale_time_frame = 30 # [s]
            desired_cpu = 0.75
            initial_server_cnt = 1
            scaling_tolerance = 0.1
            min_server = 1

            # estimation of max allowed server counts depending on load level
            max_server = int(arrival_rate / service_rate * 2)
            # the number of scaling events
            number_of_time_frames = math.ceil(simulation_length_minutes * 60 / scale_time_frame)
            cont_start = 0

            # generate load, write to file and read it back to give it to the models
            ptg = load_gen.PoissonTimeGenerator(simulation_length_minutes, arrival_rate, service_rate)
            filename = ptg.write_times_to_file(filename=load_file_name, file_extension=".out")
            load_send_times, load_wait_times, serve_times, metadata = load_gen.load_times_from_file(filename)

            # instantiate and run the continuous model
            continuous_model = MMcAnalysisBasedAutoscalePredictor(initial_server_cnt, arrival_rate, service_rate, scale_time_frame,
                                                                  desired_cpu, scaling_tolerance,
                                                                  min_pod_count=min_server, max_pod_count=max_server)
            continuous_model.write_pod_cnt_to_file(load_send_times, file_name=base_file_name + ".continuous.out")

            # instantiate and run the discrete model
            discrete_model = Model(min_server, max_server, initial_server_cnt, T=number_of_time_frames,
                                   arrival_rate=arrival_rate * scale_time_frame, serving_rate=service_rate * scale_time_frame,
                                   timeFrame=scale_time_frame, desiredCPU=desired_cpu, cont_start=cont_start,
                                   mode=Model.READ_LOAD, already_read_load=(load_send_times, load_wait_times, serve_times, metadata),
                                   tolerance=scaling_tolerance)
            discrete_model.run()
            discrete_model.write_to_file(base_file_name + ".discrete.out")

