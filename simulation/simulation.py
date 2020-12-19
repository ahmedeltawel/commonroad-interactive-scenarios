"""
SUMO simulation specific helper methods
"""
import copy
import os
import pickle
import warnings
from typing import Tuple, Union

import matplotlib as mpl
from commonroad.common.solution import Solution

from config.sumo_config import SumoConf
from sumocr.interface.sumo_simulation import SumoSimulation

mpl.use('TkAgg')

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.scenario.scenario import Scenario
from commonroad.planning.planning_problem import PlanningProblemSet

from sumocr.maps.scenario_wrapper import AbstractScenarioWrapper
from sumocr.visualization.gif import create_gif

# import necessary classes from different modules

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
                      num_of_steps: int = None,
                      planning_problem_set: PlanningProblemSet = None,
                      solution: Solution = None,
                      use_sumo_manager: bool = False) -> Scenario:
    """
    Simulates an interactive scenario with or without a solution trajectory

    :param conf: The config of the simulation
    :param scenario_wrapper: The scenario wrapper used by the Simulator
    :param scenario_dir_path: The path to the directory of the interactive scenario
    :param num_of_steps: The number of steps to simulate
    :param planning_problem_set: The planning problem set which is used by the simulator
    :param solution: The solution to simulate
    :param use_sumo_manager: Indicates whether to use the SUMO-Manager or not
    :return: The simulated scenario
    """
    simulated_scenario = None
    num_of_trials = 3
    for _ in range(num_of_trials):
        try:
            if num_of_steps is None:
                num_of_steps = conf.simulation_steps

            sumo_interface = None
            if use_sumo_manager:
                try:
                    from commonroad_sumo_manager.crsumo.interface.sumo_interface import SumoInterface
                except ImportError:
                    SumoInterface = None
                    raise ImportError("CommonRoad SUMO Manager not installed!")

                sumo_interface = SumoInterface(use_docker=True)
                sumo_sim = sumo_interface.start_simulator()

                sumo_sim.send_sumo_scenario(conf.scenario_name,
                                            scenario_dir_path)
            else:
                sumo_sim = SumoSimulation()

            if planning_problem_set is not None:
                sumo_sim.planning_problem_set = planning_problem_set

            # initialize sumo simulation
            sumo_sim.initialize(conf, scenario_wrapper)

            # runs the simulation
            def run_simulation():
                for step in range(num_of_steps):
                    # plan trajectories for all ego vehicles
                    if solution:
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
                            ego_trajectory = [next_state]
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

        except Exception as e:
            warnings.warn(f"Unsuccessful simulation, trying again: {e}")

    if simulated_scenario is None:
        raise RuntimeError("Unexpected errors occurred during the simulation!")


def simulate_scenario2(mode: int,
                       conf: SumoConf,
                       scenario_wrapper: AbstractScenarioWrapper,
                       scenario_path: str,
                       num_of_steps: int = None,
                       planning_problem_set: PlanningProblemSet = None,
                       solution: Solution = None,
                       use_sumo_manager: bool = False) -> Union[Scenario, None]:
    """
    Simulates an interactive scenario with specified mode

    :param mode: 0 = without ego, 1 = with plugged in planner, 2 = with solution trajectory
    :param conf: config of the simulation
    :param scenario_wrapper: scenario wrapper used by the Simulator
    :param scenario_path: path to the interactive scenario folder
    :param num_of_steps: number of steps to simulate
    :param planning_problem_set: planning problem set of the scenario
    :param solution: solution to the planning problem
    :param use_sumo_manager: indicates whether to use the SUMO Manager
    :return: simulated scenario
    """

    if use_sumo_manager:
        raise NotImplementedError("Usage of SUMO Manager not supported yet.")

    if num_of_steps is None:
        num_of_steps = conf.simulation_steps

    simulated_scenario = None
    num_of_trials = 5

    for _ in range(num_of_trials):
        try:
            sumo_interface = None
            if use_sumo_manager:
                try:
                    from commonroad_sumo_manager.crsumo.interface.sumo_interface import SumoInterface
                except ImportError:
                    SumoInterface = None
                    raise ImportError("CommonRoad SUMO Manager not installed!")

                sumo_interface = SumoInterface(use_docker=True)
                sumo_sim = sumo_interface.start_simulator()

                sumo_sim.send_sumo_scenario(conf.scenario_name,
                                            scenario_path)
            else:
                sumo_sim = SumoSimulation()

            if planning_problem_set is not None:
                sumo_sim.planning_problem_set = planning_problem_set

            # initialize simulation
            sumo_sim.initialize(conf, scenario_wrapper)

            if mode == 0:
                # simulation without ego vehicle
                for step in range(num_of_steps):
                    # set to dummy simulation
                    sumo_sim.dummy_ego_simulation = True
                    sumo_sim.simulate_step()

            elif mode == 1:
                # simulation with plugged in planner
                pass

            elif mode == 2:
                # simulation with given solution trajectory
                ego_vehicles = sumo_sim.ego_vehicles

                # check if the given solution is valid
                for idx, ego_vehicle in enumerate(ego_vehicles.values()):
                    trajectory_next_ego = solution.planning_problem_solutions[idx].trajectory

                    if len(trajectory_next_ego.state_list) < num_of_steps:
                        raise Exception("Given solution has less time steps than required for simulation.")

                # simulate
                for step in range(num_of_steps):
                    for idx, ego_vehicle in enumerate(ego_vehicles.values()):
                        trajectory_solution = solution.planning_problem_solutions[idx].trajectory

                        # copy a state from the solution trajectory, and convert it into a trajectory with only 1 state
                        state_next_ego = copy.deepcopy(trajectory_solution.state_list[step])
                        state_next_ego.time_step = 1
                        trajectory_next_ego = [state_next_ego]
                        ego_vehicle.set_planned_trajectory(trajectory_next_ego)

                        if use_sumo_manager:
                            # set the modified ego vehicles to synchronize in case of using SUMO Manager
                            sumo_sim.ego_vehicles = ego_vehicles

                    sumo_sim.simulate_step()

            # retrieve the simulated scenario in CR format
            simulated_scenario = sumo_sim.commonroad_scenarios_all_time_steps()

            # stop the simulation
            sumo_sim.stop()
            if use_sumo_manager:
                sumo_interface.stop_simulator()

            return simulated_scenario

        except Exception as e:
            warnings.warn(f"Unsuccessful simulation, trying again: {e}")

    if simulated_scenario is None:
        raise RuntimeError("Unexpected errors occurred during the simulation.")


def simulate_without_ego(interactive_scenario_path: str,
                         output_folder_path: str = None,
                         create_GIF: bool = False,
                         use_sumo_manager: bool = False) -> Tuple[Scenario, PlanningProblemSet]:
    """
    Simulates an interactive scenario without ego vehicle

    :param interactive_scenario_path: path to the interactive scenario folder
    :param output_folder_path: path to the output folder
    :param create_GIF: indicates whether to create a GIF of the simulated scenario
    :param use_sumo_manager: indicates whether to use the SUMO-Manager
    :return: Tuple of the simulated scenario and the planning problem set
    """
    with open(os.path.join(interactive_scenario_path, "simulation_config.p"), "rb") as input_file:
        conf = pickle.load(input_file)

    scenario_file = os.path.join(interactive_scenario_path, f"{conf.scenario_name}.cr.xml")
    scenario, planning_problem_set = CommonRoadFileReader(scenario_file).open()

    scenario_wrapper = AbstractScenarioWrapper()
    scenario_wrapper.sumo_cfg_file = os.path.join(interactive_scenario_path, f"{conf.scenario_name}.sumo.cfg")
    scenario_wrapper.lanelet_network = scenario.lanelet_network

    # simulation without ego vehicle
    simulated_scenario_without_ego = simulate_scenario2(0, conf,
                                                        scenario_wrapper,
                                                        interactive_scenario_path,
                                                        num_of_steps=conf.simulation_steps,
                                                        planning_problem_set=planning_problem_set,
                                                        solution=None,
                                                        use_sumo_manager=use_sumo_manager)
    simulated_scenario_without_ego.scenario_id = scenario.scenario_id

    if create_GIF:
        if not output_folder_path:
            print("Output folder not specified, skipping GIF generation.")
        else:
            for idx, planning_problem in enumerate(planning_problem_set.planning_problem_dict.values()):
                create_gif(simulated_scenario_without_ego,
                           output_folder_path,
                           planning_problem=planning_problem,
                           trajectory=None,
                           follow_ego=True)

    return simulated_scenario_without_ego, planning_problem_set


def simulate_with_solution(interactive_scenario_path: str,
                           output_folder_path: str = None,
                           solution: Solution = None,
                           create_GIF: bool = False,
                           use_sumo_manager: bool = False) -> Tuple[Scenario, PlanningProblemSet]:
    """
    Simulates an interactive scenario with a given solution

    :param interactive_scenario_path: path to the interactive scenario folder
    :param output_folder_path: path to the output folder
    :param solution: solution to the planning problem
    :param create_GIF: indicates whether to create a GIF of the simulated scenario
    :param use_sumo_manager: indicates whether to use the SUMO-Manager
    :return: Tuple of the simulated scenario and the planning problem set
    """
    if not isinstance(solution, Solution):
        raise Exception("Solution to the planning problem is not given.")

    with open(os.path.join(interactive_scenario_path, "simulation_config.p"), "rb") as input_file:
        conf = pickle.load(input_file)

    scenario_file = os.path.join(interactive_scenario_path, f"{conf.scenario_name}.cr.xml")
    scenario, planning_problem_set = CommonRoadFileReader(scenario_file).open()

    scenario_wrapper = AbstractScenarioWrapper()
    scenario_wrapper.sumo_cfg_file = os.path.join(interactive_scenario_path, f"{conf.scenario_name}.sumo.cfg")
    scenario_wrapper.lanelet_network = scenario.lanelet_network

    # simulation without ego vehicle
    simulated_scenario_with_solution = simulate_scenario2(2, conf,
                                                          scenario_wrapper,
                                                          interactive_scenario_path,
                                                          num_of_steps=conf.simulation_steps,
                                                          planning_problem_set=planning_problem_set,
                                                          solution=solution,
                                                          use_sumo_manager=use_sumo_manager)
    simulated_scenario_with_solution.scenario_id = scenario.scenario_id

    if create_GIF:
        if not output_folder_path:
            print("Output folder not specified, skipping GIF generation.")
        else:
            for idx, planning_problem in enumerate(planning_problem_set.planning_problem_dict.values()):
                create_gif(simulated_scenario_with_solution,
                           output_folder_path,
                           planning_problem=planning_problem,
                           trajectory=solution.planning_problem_solutions[idx].trajectory,
                           follow_ego=True,
                           mode=2)

    return simulated_scenario_with_solution, planning_problem_set
