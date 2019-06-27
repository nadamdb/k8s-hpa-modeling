import math
import os
import argparse

from continuous_model.autoscale_predictor import AdaptiveRateEstimatingMMcBasedAutoscalePredictor
from discrete_model.mymodel import Model
import generator.timegenerator as load_gen
from plotter import plotter


if __name__ == "__main__":
    # Parsing arguments, and loading data from the load file
    parser = argparse.ArgumentParser()
    parser.add_argument("--load-dir", help="Directory of the load files")
    parser.add_argument("--timeframe", help="Scale time frame [s]", type=int)
    parser.add_argument("--out-dir", help="Output directory name")
    args = parser.parse_args()

    if args.out_dir[-1] == "/":
        out_put_folder = args.out_dir + "model_outputs/"
        plots_folder = args.out_dir + "plots/"
    else:
        out_put_folder = args.out_dir + "/model_outputs/"
        plots_folder = args.out_dir + "/plots/"
    os.system("rm -rf {}".format(out_put_folder))
    os.system("rm -rf {}".format(plots_folder))

    measurement_files = os.listdir(args.out_dir)
    if args.out_dir[-1] == "/":
        measurement_files = [args.out_dir + measurement_file for measurement_file in measurement_files]
    else:
        measurement_files = [args.out_dir + "/" + measurement_file for measurement_file in measurement_files]
    measurement_files = sorted(measurement_files)

    files = os.listdir(args.load_dir)
    if args.load_dir[-1] == "/":
        files_with_path = [args.load_dir + file for file in files]
    else:
        files_with_path = [args.load_dir + "/" + file for file in files]
    files = sorted(files)
    files_with_path = sorted(files_with_path)

    os.system("mkdir -p {}".format(out_put_folder))
    os.system("mkdir -p {}".format(plots_folder))

    for i in range(0, len(files_with_path)):
        file = files[i]
        file_with_path = files_with_path[i]
        measurement_file = measurement_files[i]
        base_file_name_with_path = out_put_folder + file

        load_send_times, load_wait_times, serve_times, metadata = load_gen.load_times_from_file(file_with_path)

        simulation_length_minutes = metadata["measurement_length"]

        if "type" in metadata:
            if metadata["type"] == "mmpp":
                arrival_rate = metadata["load_rate_list"][0]
            elif metadata["type"] == "poisson":
                arrival_rate = metadata["load_rate"]
        else:
            arrival_rate = metadata["load_rate"]
        service_rate = metadata["serve_rate"]

        # autoscaling parameters
        scale_time_frame = args.timeframe
        desired_cpu = 0.75
        initial_server_cnt = 1
        scaling_tolerance = 0.1
        min_server = 1
        max_server = 20

        # TO BE ALIGNED PARAMS:
        # in our measurements downscale stabilization was always the same as the scale time frame
        downscale_stabilization_time = scale_time_frame # [s]

        # the number of scaling events
        number_of_time_frames = math.ceil(simulation_length_minutes * 60 / scale_time_frame)
        cont_start = 0

        # instantiate and run the continuous model
        continuous_model = AdaptiveRateEstimatingMMcBasedAutoscalePredictor(initial_server_cnt, arrival_rate, service_rate,
                                                                            scale_time_frame,
                                                                            desired_cpu, scaling_tolerance,
                                                                            min_pod_count=min_server, max_pod_count=max_server,
                                                                            downscale_stabilization_time=downscale_stabilization_time)
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

        # Plotting the outputs
        plotter.plot_data(plotter.get_data_from_file(measurement_file),
                          plotter.get_data_from_file(base_file_name_with_path + ".discrete.out"),
                          plotter.get_data_from_file(base_file_name_with_path + ".continuous.out"),
                          to_file_name=plots_folder + file)

        with open("debug.out", 'a') as debug_file:
            line = "{} | {} | {}\n".format(measurement_file,
                                           base_file_name_with_path + ".discrete.out",
                                           base_file_name_with_path + ".continuous.out")
            debug_file.write(line)
