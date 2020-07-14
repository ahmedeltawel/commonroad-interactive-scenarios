# Commonroad Interactive Benchmarks

Extend the existing non-interactive CommonRoad scenario generation methods to interative scenarios.

## Requirements

The previous work [Commonroad_Scenarios](https://gitlab.lrz.de/ss19/commonroad_scenarios) needs to be installed properly.

## interactive_scenarios_genaration.py

Define the class `GenerateCRScenarios_I` inheriting the class `GenerateCRScenarios` in [cr_scenario_generation.py](https://gitlab.lrz.de/ss19/commonroad_scenarios/-/blob/master/scenario_generation/cr_scenario_generation.py).

Overload some methods to keep only the initial states for interaction and extend the scenario benchmark Ids with mark **I**.

## Generate interactive CommonRoad scenarios using SUMO
An example can be found in `example.py`
