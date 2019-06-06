import math

from continuous_model.autoscale_predictor import AdaptiveRateEstimatingMMcBasedAutoscalePredictor
from discrete_model.mymodel import Model
import generator.timegenerator as load_gen


if __name__ == "__main__":
    for arrival_rate in [10, 15, 20, 30]:
        for service_rate in [1, 2]:
            for seed in [0,1,2]:
                # Load parameters
                print("\nSIMULATION ROUND: arrival rate: {}, service rate: {}".format(arrival_rate, service_rate))
                simulation_length_minutes = 30 # [min]
                out_put_folder = "working/measurement_2/model_outputs/"

                # autoscaling parameters
                scale_time_frame = 15 # [s]
                desired_cpu = 0.75
                initial_server_cnt = 1
                scaling_tolerance = 0.1
                min_server = 1
                max_server = 20

                # the number of scaling events
                number_of_time_frames = math.ceil(simulation_length_minutes * 60 / scale_time_frame)
                cont_start = 0

                # generate load, write to file and read it back to give it to the models
                ptg = load_gen.PoissonTimeGenerator(simulation_length_minutes, arrival_rate, service_rate, random_seed=seed)
                # The load generator creates a file name
                base_file_name_with_path = out_put_folder + ptg.name
                filename = ptg.write_times_to_file(filename=base_file_name_with_path, file_extension=".out")
                load_send_times, load_wait_times, serve_times, metadata = load_gen.load_times_from_file(filename)

                # instantiate and run the continuous model
                continuous_model = AdaptiveRateEstimatingMMcBasedAutoscalePredictor(initial_server_cnt, arrival_rate, service_rate,
                                                                                    scale_time_frame,
                                                                                    desired_cpu, scaling_tolerance,
                                                                                    min_pod_count=min_server, max_pod_count=max_server)
                continuous_model.write_pod_cnt_to_file_adaptive(load_send_times, serve_times,
                                                                file_name=base_file_name_with_path + ".continuous.out")

                # instantiate and run the discrete model
                discrete_model = Model(min_server, max_server, initial_server_cnt, T=number_of_time_frames,
                                       arrival_rate=arrival_rate * scale_time_frame, serving_rate=service_rate * scale_time_frame,
                                       timeFrame=scale_time_frame, desiredCPU=desired_cpu, cont_start=cont_start,
                                       mode=Model.READ_LOAD, already_read_load=(load_send_times, load_wait_times, serve_times, metadata),
                                       tolerance=scaling_tolerance)
                discrete_model.run()
                discrete_model.write_to_file(base_file_name_with_path + ".discrete.out")

