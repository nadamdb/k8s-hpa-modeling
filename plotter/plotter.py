#!/usr/bin/python3

import matplotlib.pyplot as plt
import json
import argparse


def get_data_from_file(filename):
    with open(filename, "r") as file:
        return json.load(file)


def convert_prometheus_data(data):
    converted_data = {"time" : [], "data" : []}
    for i in range(0, len(data)):
        converted_data["data"].append(int(data[i][1]))
        converted_data["time"].append(i)
    return converted_data


def convert_model_data(data, timeframe):
    converted_data = {"time": [], "data": []}
    for i in range(0, len(data)):
        converted_data["data"].append(data[i])
        converted_data["time"].append(i * timeframe)
    return converted_data


def plot_data(k8s_log=None, model_log=None, cont_model_pod_count=None, base_model_pod_count=None, to_file_name=None):
    fig, ax = plt.subplots()
    if model_log is not None:
        model_pod_count = convert_model_data(model_log["data"]["server_count"], model_log["metadata"]["timeframe_length"])
        model_mean = sum(model_pod_count["data"]) / len(model_pod_count["data"])

        ax.axhline(model_mean, color="red", linestyle="--", label="disc. model mean")
        ax.plot(model_pod_count["time"], model_pod_count["data"], label="discrete model", color="red")

    if k8s_log is not None:
        if model_log is None:
            raise NotImplementedError("Kubernetes log file cannot be plotted without the discrete model output")
        # Process kubernetes log format
        k8s_pod_count = convert_prometheus_data(k8s_log["data"]["pod_count"])
        k8s_hpa_current = convert_prometheus_data(k8s_log["data"]["hpa_current"])
        k8s_hpa_desired = convert_prometheus_data(k8s_log["data"]["hpa_desired"])

        k8s_pod_count["data"] = k8s_pod_count["data"][:model_pod_count["time"][len(model_pod_count["time"]) - 1]]
        k8s_pod_count["time"] = k8s_pod_count["time"][:model_pod_count["time"][len(model_pod_count["time"]) - 1]]

        k8s_mean = sum(k8s_pod_count["data"]) / len(k8s_pod_count["data"])

        # Plot its data
        ax.axhline(k8s_mean, color="blue", linestyle="--", label="real measurement mean")
        ax.plot(k8s_pod_count["time"], k8s_pod_count["data"], label="real measurement", color="blue")

        # ax.plot(k8s_hpa_current["time"], k8s_hpa_current["data"], label="hpa current", color="green")
        # ax.plot(k8s_hpa_desired["time"], k8s_hpa_desired["data"], label="hpa desired", color="yellow")

    if cont_model_pod_count is not None:
        # continuous model output is in the required format already
        cont_model_mean = sum(cont_model_pod_count["data"]) / len(cont_model_pod_count["data"])
        ax.axhline(cont_model_mean, color="green", linestyle="--", label="cont. model mean")
        ax.plot(cont_model_pod_count["time"], cont_model_pod_count["data"], label="continuous model", color="green")

    if base_model_pod_count is not None:
        # baseline model output is in the required format already
        cont_model_mean = sum(base_model_pod_count["data"]) / len(base_model_pod_count["data"])
        ax.axhline(cont_model_mean, color="yellow", linestyle="--", label="cont. model mean")
        ax.plot(base_model_pod_count["time"], base_model_pod_count["data"], label="baseline model", color="yellow")

    plt.xlabel("Time [sec]")
    plt.ylabel("Number of pods")
    ax.legend(loc='lower right')

    if to_file_name is not None:
        plt.savefig(to_file_name + ".png")
    else:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--k8s-log", help="Logfile of the cluster measurement", default=None)
    parser.add_argument("--model-log", help="Logfile of the discrete model", default=None)
    parser.add_argument("--cont-model-log", help="Logfile of the continuous model", default=None)
    parser.add_argument("--base-model-log", help="Logfile of the baseline continuous model", default=None)
    parser.add_argument("--file-name", help="Save the generated figures to file", default=None)
    args = parser.parse_args()

    cont_model_pod_count, k8s_log, disc_model_log = None, None, None
    if args.cont_model_log is not None:
        cont_model_pod_count = get_data_from_file(args.cont_model_log)
    if args.base_model_log is not None:
        base_model_pod_count = get_data_from_file(args.base_model_log)
    if args.k8s_log is not None:
        k8s_log = get_data_from_file(args.k8s_log)
    if args.model_log is not None:
        disc_model_log = get_data_from_file(args.model_log)

    if k8s_log is None and disc_model_log is None and cont_model_pod_count is None:
        raise FileNotFoundError

    plot_data(k8s_log, disc_model_log, cont_model_pod_count, base_model_pod_count, to_file_name=args.file_name)
