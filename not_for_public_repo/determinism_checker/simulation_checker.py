"""
Check the determinism of the obstacles by simulating many times
"""
import os
import pickle
import random
import warnings
from collections import defaultdict
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario
from commonroad.visualization.draw_dispatch_cr import draw_object
from sumocr.maps.sumo_scenario import ScenarioWrapper
from sumocr.maps.sumo_scenario import ScenarioWrapper
from sumocr.visualization.video import create_video

from common.simulation import simulate_scenario

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


def get_variable_lists(obstacle: DynamicObstacle) -> Dict[str, list]:
    """
    Get necessary variables from dynamic obstacle states
    :param obstacle: The dynamic obstacle
    :return: Dictionary of list of states
    """
    state_list = obstacle.prediction.trajectory.state_list
    variable_lists = {'accel': [state.acceleration for state in state_list],
                      'v': [state.velocity for state in state_list],
                      "pos_x": [state.position[0] for state in state_list],
                      'pos_y': [state.position[1] for state in state_list],
                      'orientation': [state.orientation for state in state_list]}
    return variable_lists


def obstacle_determinism_check(simulated_scenarios: Dict[int, Scenario],
                               std_tolerance: float = 0.1) -> bool:
    """
    Check determinism by comparing states of all vehicles between simulated scenarios
    :param simulated_scenarios: The simulated scenarios
    :param std_tolerance: The tolerance of the average standard deviation
    :return Boolean indicates whether the simulation was deterministic or not
    """

    is_deterministic = True
    obstacle_trajectories = defaultdict(lambda: [])
    determinism_statistics = dict()

    for simulation_id, scenario in simulated_scenarios.items():
        for obstacle in scenario.dynamic_obstacles:
            trajectory_states = get_variable_lists(obstacle)
            obstacle_trajectories[obstacle.obstacle_id].append(list(trajectory_states.values()))

    for obstacle_id, obstacle_trajectory_values in obstacle_trajectories.items():
        # Convert to numpy array to prepare for statistical evaluation
        obstacle_trajectory_values = np.array(obstacle_trajectory_values)

        if obstacle_trajectory_values.ndim != 3:
            is_deterministic = False
            trajectory_shapes = [np.array(list(obstacle_simulation_values)).shape for
                                 obstacle_simulation_values in
                                 obstacle_trajectory_values]
            print(f"Obstacle found with different number of states: "
                  f"{obstacle_id} - "
                  f"{trajectory_shapes}")
            continue

        # Calculate the average standard deviation of the positions
        determinism_statistics.update(
            {obstacle_id: np.average(np.std(obstacle_trajectory_values, axis=0), axis=1)})

    if len(determinism_statistics) > 0:
        if np.max(np.array(list(determinism_statistics.values()))) > std_tolerance:
            is_deterministic = False
            print(
                f"The vehicles are not deterministic, average standard deviation values: {determinism_statistics}")

    if is_deterministic:
        print("The vehicles are deterministic.")

    return is_deterministic


def plot_vehicle_trajectories(simulated_scenarios: Dict[int, Scenario], vehicle_id: int = None):
    """
    Plot the trajectories of one vehicle in each scenario
    :param simulated_scenarios: Dictionary of the simulated scenarios by the simulation ID
    :param vehicle_id: The ID of the vehicle which will be plotted. If None, then randomly chosen
    """
    if len(simulated_scenarios) == 0:
        return

    inch_in_cm = 2.54
    figsize = [16, 9]
    dpi = 200

    if vehicle_id is None:
        vehicle_id_list = [obstacle.obstacle_id for obstacle in
                           list(simulated_scenarios.values())[0].dynamic_obstacles]
        vehicle_id = random.choice(vehicle_id_list)  # choose an arbitrary vehicle id
    # TODO: Implement feature to merge plots
    for simulation_id, scenario in simulated_scenarios.items():
        obstacle = scenario.obstacle_by_id(vehicle_id)

        fig = plt.figure(figsize=(figsize[0] / inch_in_cm, figsize[1] / inch_in_cm), dpi=dpi)
        fig.gca().axis('equal')
        plt.title(f"Trajectory of vehicle {vehicle_id} in simulation {simulation_id}", fontsize=12,
                  color='k')

        handles = {}  # collects handles of obstacle patches, plotted by matplotlib
        draw_object(scenario, handles=handles, draw_params={'time_begin': -1, 'time_end': -1})

        for occupancy in obstacle.prediction.occupancy_set:
            draw_object(occupancy.shape)

        fig.gca().autoscale()

    plt.show()


def resimulate_scenario(scenario_folder_path: str,
                        num_of_simulations: int,
                        use_sumo_manager: bool = False,
                        creating_video: bool = False,
                        output_folder_path: str = None) -> Dict[int, Scenario]:
    """
    Simulating a scenario many times for determinsim check and returning the simulated scenarios
    :param scenario_file_path: Path to the interactive scenario
    :param num_of_simulations: The number of simulations whioch will be performed for statistics gathering
    :param use_sumo_manager: Indicates whether to use the sumo-manager
    :param creating_video: Indicates whether to create video
    :param output_folder_path: Path to the output folder for the videos
    :return: Dictionary of the simulated scenarios by the simulation ID
    """

    assert not creating_video or output_folder_path is not None, \
        "The output folder path was not defined for video creation"

    with open(os.path.join(scenario_folder_path, "simulation_config.p"), "rb") as input_file:
        conf = pickle.load(input_file)

    scenario_file = os.path.join(scenario_folder_path, f"{conf.scenario_name}.cr.xml")
    scenario, planning_problem_set = CommonRoadFileReader(scenario_file).open()

    scenario_wrapper = ScenarioWrapper()
    scenario_wrapper.sumo_cfg_file = os.path.join(scenario_folder_path,
                                                  f"{conf.scenario_name}.sumo.cfg")
    scenario_wrapper.initial_scenario = scenario

    simulated_scenarios = dict()  # store simulated example_scenarios for every simulation

    #########################
    # Simulation and record #
    #########################
    for simulation_id in range(num_of_simulations):
        print(f"Simulation {simulation_id} start.")
        simulated_scenario = simulate_scenario(conf, scenario_wrapper, scenario_folder_path,
                                               use_sumo_manager=use_sumo_manager)
        simulated_scenarios.update({simulation_id: simulated_scenario})

        if creating_video:
            create_video(simulated_scenario, output_folder_path)

    return simulated_scenarios
