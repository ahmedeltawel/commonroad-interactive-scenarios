"""
Check the determinism of the obstacles by simulating many times
"""
import os
import random
from collections import defaultdict
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario
from commonroad.visualization.draw_dispatch_cr import draw_object
from cr2sumo.interface.sumo_interface import SumoInterface
from cr2sumo.visualization.video import create_video as create_video_sumo_manager
from scenario_generation.config_files.sumo_config import SumoConf
from sumo2cr.interface.sumo_simulation import SumoSimulation
from sumo2cr.maps.sumo_scenario import ScenarioWrapper
from sumo_config.default import SumoCommonRoadConfig as SumoManagerCommonRoadConfig

__author__ = "Peter Kocsis, Yueming Li"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"

from utils.benchmark_id import CRBenchmarkID


def get_variable_lists(obstacle: DynamicObstacle):
    """
    Get necessary variables from dynamic obstacle states
    :param obstacle: The dynamic obstacle
    :return List of states
    """
    state_list = obstacle.prediction.trajectory.state_list
    variable_lists = {'accel': [state.acceleration for state in state_list],
                      'v': [state.velocity for state in state_list],
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
            trajectory_shapes = [np.array(list(obstacle_simulation_values)).shape for obstacle_simulation_values in
                                 obstacle_trajectory_values]
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
        vehicle_id_list = [obstacle.obstacle_id for obstacle in list(simulated_scenarios.values())[0].dynamic_obstacles]
        vehicle_id = random.choice(vehicle_id_list)  # choose an arbitrary vehicle id
    # TODO: Implement feature to merge plots
    for simulation_id, scenario in simulated_scenarios.items():
        obstacle = scenario.obstacle_by_id(vehicle_id)

        fig = plt.figure(figsize=(figsize[0] / inch_in_cm, figsize[1] / inch_in_cm), dpi=dpi)
        fig.gca().axis('equal')
        plt.title(f"Trajectory of vehicle {vehicle_id} in simulation {simulation_id}", fontsize=12, color='k')

        handles = {}  # collects handles of obstacle patches, plotted by matplotlib
        draw_object(scenario, handles=handles, draw_params={'time_begin': -1, 'time_end': -1})

        for occupancy in obstacle.prediction.occupancy_set:
            draw_object(occupancy.shape)

        fig.gca().autoscale()

    # plt.savefig(os.path.join(video_output_folder, conf.scenario_name + '_' + str(n+1) + '.png'),
    # format='png', dpi=300)
    # print("Trajectory x of vehicle " + str(vehicle_id_test) + " at " + str(n+1) + "th simulation is:")
    # print(list_position_x[n][str(vehicle_id_test)])

    plt.show()


def simulate_scenario(scenario_folder_path: str,
                      num_of_simulations: int,
                      use_sumo_manager: bool = False,
                      creating_video: bool = False,
                      output_folder_path: str = None) -> Dict[int, Scenario]:
    """
    Simulating a scenario many times for determinsim check and returning the simulated scenarios
    :param scenario_folder_path: Path to the folder which contains all the necessary files of the interactive scenario
    :param num_of_simulations: The number of simulations whioch will be performed for statistics gathering
    :param use_sumo_manager: Indicates whether to use the sumo-manager
    :param creating_video: Indicates whether to create video
    :param output_folder_path: Path to the output folder for the videos
    :return: Dictionary of the simulated scenarios by the simulation ID
    """

    assert not creating_video or output_folder_path is not None, \
        "The output folder path was not defined for video creation"

    if use_sumo_manager:
        # Create Interface to SUMO
        sumo_interface = SumoInterface()

        create_video_function = create_video_sumo_manager

        # TODO: Currently, the sumo manager is built with an older version of the sumo-interface, therefore the results
        #  of the simulations with and without sumo-manager won't match.
        #  Check for differences when the sumo-manager is updated!
        def create_simulator():
            simulator = sumo_interface.start_simulator()

            # upload folder contains all files needed for sumo-simulation
            simulator.send_sumo_scenario(conf.scenario_name, scenario_folder_path)
            simulator.initialize(conf)
            return simulator

        conf = SumoManagerCommonRoadConfig()

    else:
        sumo_interface = None

        create_video_function = creating_video

        def create_simulator():
            # TODO: This is a workaround for the problem that there is a hardcoded path
            #  in sumo-interface for the cr_map_file: os.path.join(os.path.dirname(__file__),'../../example_scenarios/',
            #                                        config.scenario_name, config.scenario_name + '.maps.xml')
            #  Remove if resolved!
            cr_map = os.path.join(scenario_folder_path, f"{benchmark_id}.maps.xml")
            scenario_wrapper = ScenarioWrapper.init_from_scenario(config=conf, cr_map_file=cr_map)

            simulator = SumoSimulation()
            simulator.initialize(conf, scenario_wrapper=scenario_wrapper)
            return simulator

        conf = SumoConf()
        conf.scenarios_path = os.path.dirname(scenario_folder_path)

    benchmark_id = CRBenchmarkID.from_path(scenario_folder_path)
    conf.scenario_name = str(benchmark_id)  # given scenario name

    simulated_scenarios = dict()  # store simulated example_scenarios for every simulation

    #########################
    # Simulation and record #
    #########################
    for simulation_id in range(num_of_simulations):
        print(f"Simulation {simulation_id} start.")

        sumo_sim = create_simulator()
        sumo_sim._dummy_ego_simulation = True
        for step in range(conf.simulation_steps):
            sumo_sim.simulate_step()
        sumo_sim.stop()
        # record simulated example_scenarios
        simulated_scenario = sumo_sim.commonroad_scenarios_all_time_steps()
        simulated_scenarios.update({simulation_id: simulated_scenario})

        if creating_video:
            create_video_function(sumo_sim, conf.video_start, conf.video_end, output_folder_path)

    if use_sumo_manager:
        sumo_interface.stop_simulator()

    return simulated_scenarios
