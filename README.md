# Commonroad Interactive Benchmarks

Extend the existing non-interactive CommonRoad scenario generation methods to interative scenarios.

## Requirements

*  The previous work [Commonroad_Scenarios](https://gitlab.lrz.de/ss19/commonroad_scenarios) needs to be installed properly.

*  [SUMO-CommonRoad Interface](https://gitlab.lrz.de/cps/sumo-interface/-/tree/interactive_SS20)

*  [commonroad-sumo-manager](https://gitlab.lrz.de/cps/commonroad-sumo-manager), if needed.

## Installation

This project should be run with conda. Make sure it is installed before proceeding with the installation.

To create an environment for this project including all requirements, run
```
conda env create -n cr37 -f environment.yml
```


To install the requirements of the module, simply run
```
bash install.sh cr37
```
`cr37` to be replaced by the name of your conda environment if needed.

## interactive_scenarios_genaration.py

Define the class `GenerateCRScenarios_I` inheriting the class `GenerateCRScenarios` in [cr_scenario_generation.py](https://gitlab.lrz.de/ss19/commonroad_scenarios/-/blob/master/scenario_generation/cr_scenario_generation.py).

Overload some methods to keep only the initial states for interaction and extend the scenario benchmark Ids with mark **I**.

## Generate interactive CommonRoad scenarios using SUMO
An example can be found in `generate_scenarios.py`

## Determinism checker
Check if a scenario is deterministic or not by two means:
*  Simulate the scenario multiple times, compare the simulated scenarios. Method defined in `simu_and_check.py`.
   
   Alternatively, can use `check_with_deviation.py`, which computes the variance instead of absolute difference when comparing the state values.

*  Read rou.xml file and check if any key parameters are set to 'random'. Method defined in `route_file_checker.py`. Run `example.py` to test.

## sumo-manager
The first determinism checker is also implemented to sumo-manger, scenarios are simulated through sumo-manager. Script `simulate_and_check.py`.