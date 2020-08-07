from pathlib import Path
import os
from route_file_checker import *

scenario_directory = 'Test' #option

filenames = list(Path(scenario_directory).rglob("*.rou.xml"))

if filenames:
    for rou_file in filenames:
        rou_file = str(rou_file)
        rou_name = os.path.basename(rou_file)
        scenario_name = rou_name.split('.')[0]
        print("Checking " + rou_name + " .")
        if rou_file_determinism_check(rou_file):
            print("Scenario " + scenario_name + " should be deterministic.")
        else:
            print("Scenario " + scenario_name + " may not be deterministic.") 
else:
    print("There is no rou file in the directory.")
    
