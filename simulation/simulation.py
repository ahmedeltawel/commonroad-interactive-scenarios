"""
SUMO simulation specific helper methods
"""
import copy
import warnings

from commonroad.common.solution import Solution
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Scenario

from config.sumo_config import SumoConf
from sumocr.interface.sumo_simulation import SumoSimulation
from sumocr.maps.scenario_wrapper import AbstractScenarioWrapper

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
    Simulates an interactive scenario with or wtihout a solution trajectory
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
