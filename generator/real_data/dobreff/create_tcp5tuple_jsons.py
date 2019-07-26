import pandas as pd
import numpy as np
import json

df_de_sep = pd.read_parquet('tcp5tuple_http_de.parquet')
df_du_sep = pd.read_parquet('tcp5tuple_http_du.parquet')

data_all_de = {}
data_all_de["load_send_time"] = df_de_sep.timestamp_start.to_list()
data_all_de["load_wait_time"] = df_de_sep.difference.to_list()[1:]
metadata_all_de = {"load_from" : "all",
                   "measurement_length" : 2,
                   "time_period_start" : "2018-10-17 07:00:00",
                   "time_period_end" : "2018-10-17 09:00:00"}
all_de_json = {"metadata" : metadata_all_de, "data" : data_all_de}

with open('tcp5tuple_http_de.json', 'w') as f:
    json.dump(all_de_json, f)

data_all_du = {}
data_all_du["load_send_time"] = df_du_sep.timestamp_start.to_list()
data_all_du["load_wait_time"] = df_du_sep.difference.to_list()[1:]
metadata_all_du = {"load_from" : "all",
                   "measurement_length" : 2,
                   "time_period_start" : "2018-10-17 11:00:00",
                   "time_period_end" : "2018-10-17 13:00:00"}
all_du_json = {"metadata" : metadata_all_du, "data" : data_all_du}

with open('tcp5tuple_http_du.json', 'w') as f:
    json.dump(all_du_json, f)
