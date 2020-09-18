"""
Check the determinism of example_scenarios by comparing difference of state values
"""
import argparse
import os
import copy
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
import random
import numpy as np

from commonroad.visualization.draw_dispatch_cr import draw_object
from commonroad.scenario.trajectory import State
from commonroad.visualization.scenario import draw_scenario
from sumo2cr.interface.sumo_simulation import SumoSimulation
from sumo2cr.maps.sumo_scenario import ScenarioWrapper

from determinism_checker.route_file_checker import rou_file_determinism_check
from scenario_generation.config_files.sumo_config import SumoConf
from commonroad.scenario.scenario import Scenario, LaneletNetwork
from commonroad.scenario.obstacle import DynamicObstacle
from sumo2cr.visualization.video import create_video

__author__ = "Yueming Li, Peter Kocsis"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"

from utils.benchmark_id import CRBenchmarkID


def check_determinism_argsparser() -> argparse.ArgumentParser:
    """Returns a parser for the script's arguments"""
    parser = argparse.ArgumentParser()
    # arguments.scenario_file_path,
    # num_of_simulations = arguments.num_of_simulations,
    # output_folder_path = arguments.output_folder_path,
    # creating_video = arguments.creating_video)
    parser.add_argument(
        "-i", "--scenario_folder_path", type=str, default=os.path.join(os.getcwd(),
                                                                     "Scenarios",
                                                                     "CHN_Cho-1-1",
                                                                     "CHN_Cho-1_1_I"),
        help="Path to the folder contains the scenario which should be checked"
    )
    parser.add_argument(
        "-ns", "--num_of_simulations", type=int, default=2, help="Number of simulations used during determinism check"
    )
    parser.add_argument(
        "-o", "--output_folder_path", type=str, default=os.path.join(os.getcwd(), "determinism_check")
        , help="Path to the output folder for the videos"
    )
    parser.add_argument(
        "-v", "--video", action="store_true", default=False, help="Create video",
    )
    return parser


def get_variable_lists(obstacle: DynamicObstacle):
    """
    Get necessary variables from dynamic obstacle states
    :param obstacle: The dynamic obstacle
    :return List of states
    """
    state_list = obstacle.prediction.trajectory.state_list
    variable_lists = {'accel': [state.acceleration for state in state_list],
                      'v':     [state.velocity for state in state_list],
                      "pos_x": [state.position[0] for state in state_list],
                      'pos_y': [state.position[1] for state in state_list],
                      'orientation': [state.orientation for state in state_list]}
    return variable_lists


def obstacle_determinism_check(simulated_scenarios: Dict[int, Scenario], std_tolerance: float = 0.1) -> bool:
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
            trajectory_shapes = [np.array(list(obstacle_simulation_values)).shape for obstacle_simulation_values in obstacle_trajectory_values]
            print(f"Obstacle found with different number of states: "
                  f"{obstacle_id} - "
                  f"{trajectory_shapes}")
            continue

        # Calculate the average standard deviation of the positions
        determinism_statistics.update({obstacle_id: np.average(np.std(obstacle_trajectory_values, axis=0), axis=1)})

    if len(determinism_statistics) > 0:
        if np.max(np.array(list(determinism_statistics.values()))) > std_tolerance:
            is_deterministic = False
            print(f"The vehicles are not deterministic, average standard deviation values: {determinism_statistics}")

    if is_deterministic:
        print("The vehicles are deterministic.")

    return is_deterministic


def plot_vehicle_trajectories(simulated_scenarios: Dict[int, Scenario], vehicle_id: int = None):
    #########################################################
    # Plot the trajectories of one vehicle in each scenario #
    #########################################################
    if len(simulated_scenarios) == 0:
        return

    # plt.style.use('classic')
    inch_in_cm = 2.54
    figsize = [16, 9]
    dpi = 200

    if vehicle_id is None:
        vehicle_id_list = [obstacle.obstacle_id for obstacle in list(simulated_scenarios.values())[0].dynamic_obstacles]
        vehicle_id = random.choice(vehicle_id_list)  # choose an arbitrary vehicle id
    # TODO: Implement feature to merge plots
    for simulation_id, scenario in simulated_scenarios.items():
        obstacle = scenario.obstacle_by_id(vehicle_id)
        vehicle_state_list =  obstacle.prediction.trajectory.state_list
        vehicle_positions_x, vehicle_positions_y = [state.position[0] for state in vehicle_state_list], \
                                                   [state.position[1] for state in vehicle_state_list]

        fig = plt.figure(figsize=(figsize[0] / inch_in_cm, figsize[1] / inch_in_cm), dpi=dpi)
        fig.gca().axis('equal')
        plt.title(f"Trajectory of vehicle {vehicle_id} in simulation {simulation_id}", fontsize=12, color='k')

        handles = {}  # collects handles of obstacle patches, plotted by matplotlib
        draw_object(scenario, handles=handles, draw_params={'time_begin': -1, 'time_end': -1})

        for occupancy in obstacle.prediction.occupancy_set:
            draw_object(occupancy.shape)

        fig.gca().autoscale()

    # plt.savefig(os.path.join(video_output_folder, conf.scenario_name + '_' + str(n+1) + '.png'), format='png', dpi=300)
    # print("Trajectory x of vehicle " + str(vehicle_id_test) + " at " + str(n+1) + "th simulation is:")
    # print(list_position_x[n][str(vehicle_id_test)])

    plt.show()


def simulate_scenario(scenario_folder_path: str,
                      num_of_simulations: int) -> Tuple[Dict[int, SumoSimulation], SumoConf]:
    benchmark_id = CRBenchmarkID.from_path(scenario_folder_path)

    conf = SumoConf()
    conf.scenario_name = str(benchmark_id)  # given scenario name
    conf.scenarios_path = os.path.dirname(scenario_folder_path)

    cr_map = os.path.join(scenario_folder_path, f"{benchmark_id}.maps.xml")
    scenario_wrapper = ScenarioWrapper.init_from_scenario(config=conf, cr_map_file=cr_map)

    simulations = dict()

    simulated_scenarios = dict()  # store simulated example_scenarios for every simulation

    #########################
    # Simulation and record #
    #########################
    for simulation_id in range(num_of_simulations):
        print(f"Simulation {simulation_id} start.")
        sumo_sim = SumoSimulation()
        sumo_sim.initialize(conf, scenario_wrapper=scenario_wrapper)
        sumo_sim._dummy_ego_simulation = True
        for step in range(conf.simulation_steps):
            sumo_sim.simulate_step()
        sumo_sim.stop()
        # record simulated example_scenarios
        simulations.update({simulation_id: sumo_sim})
        simulated_scenario = sumo_sim.commonroad_scenarios_all_time_steps()
        simulated_scenarios.update({simulation_id: simulated_scenario})

    return simulations, conf


def check_determinism(scenario_folder_path: str,
                      num_of_simulations: int,
                      output_folder_path: str,
                      creating_video: bool = False,
                      std_tolerance: float = 0.1) -> bool:
    simulations, conf = simulate_scenario(scenario_folder_path, num_of_simulations)

    # Create
    if creating_video:
        for simulation_id, simulation in simulations.items():
            create_video(simulation, conf.video_start, conf.video_end, output_folder_path)

    simulated_scenarios = {simulation_id: simulation.commonroad_scenarios_all_time_steps()
                           for simulation_id, simulation in simulations.items()}

    # Plot trajectories
    plot_vehicle_trajectories(simulated_scenarios, vehicle_id=33)

    # Check rou files for determinism
    print("Checking the route files")
    filenames = list(Path(scenario_folder_path).rglob("*.rou.xml"))
    if filenames:
        is_rou_files_deterministic = [rou_file_determinism_check(str(rou_file)) for rou_file in filenames]
        if all(is_rou_files_deterministic):
            is_rou_files_deterministic = True
            print("The rou files are deterministic")
        else:
            is_rou_files_deterministic = False
            print("The rou files are not deterministic")
    else:
        is_rou_files_deterministic = False
        print(f"No rou file has been found in {scenario_folder_path}")

    # Check vehicles for determinism
    print("Checking the obstacles' trajectories")
    is_vehicle_deterministic = obstacle_determinism_check(simulated_scenarios, std_tolerance)

    is_deterministic = is_vehicle_deterministic and is_rou_files_deterministic
    if is_deterministic:
        print("The scenario is deterministic.")

    return is_deterministic


if __name__ == '__main__':
    arguments = check_determinism_argsparser().parse_args(sys.argv[1:])
    check_determinism(scenario_folder_path=arguments.scenario_folder_path,
                      num_of_simulations=arguments.num_of_simulations,
                      output_folder_path=arguments.output_folder_path,
                      creating_video=arguments.video)
