"""
Check the determinism of the obstacles by simulating many times
"""
import copy
import os
import pickle
import random
import warnings
from collections import defaultdict
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np

from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario, ScenarioID
from commonroad.scenario.trajectory import State
from commonroad.visualization.draw_dispatch_cr import draw_object
from scenario_generation.config_files.sumo_config import SumoConf
from sumocr.maps.scenario_wrapper import AbstractScenarioWrapper
from sumocr.maps.sumo_scenario import ScenarioWrapper

from configuration import CONFIG_TYPE, get_interactive_scenario_configuration

from sumocr.interface.sumo_simulation import SumoSimulation
from sumocr.visualization.gif import create_gif

try:
    from commonroad_sumo_manager.crsumo.interface.sumo_interface import SumoInterface
    from commonroad_sumo_manager.crsumo.rpc.sumo_client import SumoRPCClient
except ImportError as exp:
    warnings.warn("CommonRoad-SUMO-Manager is not installed, the usage is not supported!")

__author__ = "Peter Kocsis, Yueming Li"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"


def simulate_scenario(conf: SumoConf,
                      scenario_wrapper: AbstractScenarioWrapper,
                      scenario_dir_path: str,
                      num_of_steps=None,
                      planning_problem_set=None,
                      solution=None,
                      use_sumo_manager: bool = False):

    if num_of_steps is None:
        num_of_steps = conf.simulation_steps

    sumo_interface = None
    if use_sumo_manager:
        sumo_interface = SumoInterface(use_docker=True)
        sumo_sim = sumo_interface.start_simulator()

        sumo_sim.send_sumo_scenario(conf.scenario_name,
                                       scenario_dir_path)
    else:
        sumo_sim = SumoSimulation()

    sumo_sim.planning_problem_set = planning_problem_set
    sumo_sim.initialize(conf, scenario_wrapper)

    def run_simulation():
        for step in range(num_of_steps):
            # plan trajectories for all ego vehicles
            if solution is not None:
                ego_vehicles = sumo_sim.ego_vehicles
                commonroad_scenario = sumo_sim.commonroad_scenario_at_time_step(
                    sumo_sim.current_time_step)

                for idx, ego_vehicle in enumerate(ego_vehicles.values()):
                    current_state = ego_vehicle.current_state

                    # Use the solution trajectory
                    ego_trajectory = solution.planning_problem_solutions[idx].trajectory
                    if len(ego_trajectory.state_list) > step:
                        next_state = copy.deepcopy(ego_trajectory.state_list[step])
                    else:
                        return
                    next_state.time_step = 1
                    ego_trajectory: List[State] = [next_state]
                    ego_vehicle.set_planned_trajectory(ego_trajectory)

                # Set the modified ego vehicles to synchronize in case of sumo-manager
                sumo_sim.ego_vehicles = ego_vehicles
            else:
                sumo_sim.dummy_ego_simulation = True

            sumo_sim.simulate_step()

    run_simulation()

    simulated_scenario = sumo_sim.commonroad_scenarios_all_time_steps()
    sumo_sim.stop()

    if use_sumo_manager:
        sumo_interface.stop_simulator()

    return simulated_scenario
