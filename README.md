# Commonroad Interactive Benchmarks

Extend the existing non-interactive CommonRoad scenario generation methods to interative scenarios.

## Requirements

*  The previous work [Commonroad_Scenarios](https://gitlab.lrz.de/ss19/commonroad_scenarios) needs to be installed properly.

*  Install [commonroad-sumo-manager](https://gitlab.lrz.de/cps/commonroad-sumo-manager).

## interactive_scenarios_genaration.py

Define the class `GenerateCRScenarios_I` inheriting the class `GenerateCRScenarios` in [cr_scenario_generation.py](https://gitlab.lrz.de/ss19/commonroad_scenarios/-/blob/master/scenario_generation/cr_scenario_generation.py).

Overload some methods to keep only the initial states for interaction and extend the scenario benchmark Ids with mark **I**.

## Generate interactive CommonRoad scenarios using SUMO
An example can be found in `generate_scenarios.py`

## Determinism check
Check if a scenario is deterministic or not by two means:
*  Simulate the scenario through sumo-manager multiple times, compare the simulated scenarios. Method defined in ...

*  Read the rou.xml file and check if any key parameters are set to 'random'. Method defined in `determinism_checker.py`. Run the `example.py` to test.