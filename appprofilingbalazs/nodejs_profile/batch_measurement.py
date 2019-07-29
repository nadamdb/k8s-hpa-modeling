import yaml
from threading import Thread
import subprocess

def run_measurement(id):
    print('MEASUREMENT {0}'.format(id))
    subprocess.call['python3','measurement.py',str(id)]


with open('config.yaml') as config_file:
    config = yaml.safe_load(config_file)
    number_of_measurements = config['measurement']['number_of_measurements']
    for i in range(1,number_of_measurements+1):
        thread = Thread(target = run_measurement, args = (i, ))
        thread.start()
    


