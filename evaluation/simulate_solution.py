""""
Script which evaluates a solution trajectory for an interactive scenario
"""
import argparse
import copy
import pickle
import sys

import matplotlib as mpl
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.solution import CommonRoadSolutionReader
from commonroad.scenario.trajectory import State
from evaluation.visualization import create_gif
from sumocr.interface.sumo_simulation import SumoSimulation
from sumocr.visualization.video import create_video

mpl.use('TkAgg')

from sumocr.maps.util import *

# load parameters

__author__ = "Peter Kocsis"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"


def evaluate_solution_argsparser() -> argparse.ArgumentParser:
    """Returns a parser for the script's arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input_scenario", type=str,
        default="./example_scenarios/interactive/DEU_A9-2_1_I-1-1",
        help="Path to the interactive scenario"
    )
    parser.add_argument(
        "-s", "--solution", type=str,
        default="./example_scenarios/solution/KS1:SA1:DEU_A9-2_1_T-1:2018b.xml",
        help="Path to the CommonRoad solution file"
    )
    parser.add_argument(
        "-v", "--video", action="store_true", default=False, help="Create video",
    )
    return parser


def run_simulation(simulator, num_of_steps, solution):
    for t in range(num_of_steps):
        # plan trajectories for all ego vehicles
        if solution is not None:
            ego_vehicles = simulator.ego_vehicles
            commonroad_scenario = simulator.commonroad_scenario_at_time_step(
                simulator.current_time_step)

            for id, ego_vehicle in ego_vehicles.items():
                current_state = ego_vehicle.current_state

                # Use the solution trajectory
                ego_trajectory = solution.planning_problem_solutions[id].trajectory
                if len(ego_trajectory.state_list) > t:
                    next_state = copy.deepcopy(ego_trajectory.state_list[t])
                else:
                    return
                next_state.time_step = 1
                ego_trajectory: List[State] = [next_state]
                ego_vehicle.set_planned_trajectory(ego_trajectory)
        else:
            simulator._dummy_ego_simulation = True

        simulator.simulate_step()


def simulate_interactive_solution(interactive_scenario_folder: str,
                                  solution_file: str,
                                  output_folder_path: str = None,
                                  creating_video: bool = False):
    with open(os.path.join(interactive_scenario_folder, "simulation_config.p"), "rb") as input_file:
        conf = pickle.load(input_file)

    with open(os.path.join(interactive_scenario_folder, "scenario_wrapper.p"), "rb") as input_file:
        scenario_wrapper = pickle.load(input_file)
    scenario_wrapper.sumo_cfg_file = os.path.join(interactive_scenario_folder,
                                                  f"{conf.scenario_name}.sumo.cfg")

    scenario_file = os.path.join(interactive_scenario_folder, f"{conf.scenario_name}.cr.xml")
    scenario, planning_problem_set = CommonRoadFileReader(scenario_file).open()

    solution = CommonRoadSolutionReader.open(solution_file)

    # Simulate with ego
    ego_simulator = SumoSimulation()
    ego_simulator.planning_problem_set = planning_problem_set
    ego_simulator.initialize(conf, scenario_wrapper=scenario_wrapper)

    run_simulation(ego_simulator, conf.simulation_steps, solution)
    simulated_scenario_with_ego = ego_simulator.commonroad_scenarios_all_time_steps()
    simulated_scenario_with_ego.scenario_id = scenario.scenario_id

    ego_simulator.stop()

    # Simulate without ego
    intact_simulator = SumoSimulation()
    intact_simulator.planning_problem_set = planning_problem_set
    intact_simulator.initialize(conf, scenario_wrapper=scenario_wrapper)

    run_simulation(intact_simulator, ego_simulator.current_time_step, solution=None)
    simulated_scenario_without_ego = intact_simulator.commonroad_scenarios_all_time_steps()
    simulated_scenario_without_ego.scenario_id = scenario.scenario_id


    intact_simulator.stop()

    if creating_video:
        if output_folder_path is None:
            output_folder_path = os.path.dirname(solution_file)
        # create_video(ego_simulator, conf.video_start, ego_simulator.current_time_step, output_folder_path)
        for idx, planning_problem in enumerate(planning_problem_set.planning_problem_dict.values()):
            create_gif(simulated_scenario_with_ego, output_folder_path,
                       planning_problem=planning_problem,
                       trajectory=solution.planning_problem_solutions[idx].trajectory,
                       secondary_scenario=simulated_scenario_without_ego,
                       follow_ego=True)

    return simulated_scenario_without_ego, simulated_scenario_with_ego


if __name__ == '__main__':
    arguments = evaluate_solution_argsparser().parse_args(sys.argv[1:])
    simulate_interactive_solution(interactive_scenario_folder=arguments.input_scenario,
                                  solution_file=arguments.solution,
                                  creating_video=arguments.video)
