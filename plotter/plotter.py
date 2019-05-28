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


def plot_data(k8s_log, model_log, to_file=False):
    k8s_pod_count = convert_prometheus_data(k8s_log["data"]["pod_count"])
    k8s_hpa_current = convert_prometheus_data(k8s_log["data"]["hpa_current"])
    k8s_hpa_desired = convert_prometheus_data(k8s_log["data"]["hpa_desired"])
    model_pod_count = convert_model_data(model_log["data"]["server_count"], model_log["metadata"]["timeframe_length"])

    k8s_pod_count["data"] = k8s_pod_count["data"][:model_pod_count["time"][len(model_pod_count["time"]) - 1]]
    k8s_pod_count["time"] = k8s_pod_count["time"][:model_pod_count["time"][len(model_pod_count["time"]) - 1]]
    model_mean = sum(model_pod_count["data"]) / len(model_pod_count["data"])
    k8s_mean = sum(k8s_pod_count["data"]) / len(k8s_pod_count["data"])

    fig, ax = plt.subplots()
    ax.axhline(model_mean, color="red", linestyle="--", label="model mean")
    ax.axhline(k8s_mean, color="blue", linestyle="--", label="real measurement mean")
    ax.plot(model_pod_count["time"], model_pod_count["data"], label="model", color="red")
    ax.plot(k8s_pod_count["time"], k8s_pod_count["data"], label="real measurement", color="blue")
    # ax.plot(k8s_hpa_current["time"], k8s_hpa_current["data"], label="hpa current", color="green")
    # ax.plot(k8s_hpa_desired["time"], k8s_hpa_desired["data"], label="hpa desired", color="yellow")
    plt.xlabel("Time [sec]")
    plt.ylabel("Number of pods")
    ax.legend(loc='upper right')

    if to_file:
        plt.savefig("timeframe_" + str(model_log["metadata"]["timeframe_length"]) + "_rate_" + str(k8s_log["metadata"]["load_rate"]) + ".png")
    else:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--k8s-log", help="Logfile of the cluster measurement")
    parser.add_argument("--model-log", help="Logfile of the model")
    args = parser.parse_args()

    k8s_log = get_data_from_file(args.k8s_log)
    model_log = get_data_from_file(args.model_log)

    if k8s_log is None or model_log is None:
        raise FileNotFoundError

    plot_data(k8s_log, model_log, True)
