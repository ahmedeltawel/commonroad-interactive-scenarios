""""
Script which simulates a solution trajectory for an interactive scenario
"""
import argparse
import pickle
from typing import Tuple

import matplotlib as mpl
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.solution import CommonRoadSolutionReader
from commonroad.scenario.scenario import Scenario

from common.simulation import simulate_scenario
from sumocr.maps.scenario_wrapper import AbstractScenarioWrapper
from sumocr.visualization.video import create_video

mpl.use('TkAgg')
import os

# from sumocr.maps.util import *

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
        default="../example_scenarios/interactive/DEU_A9-2_1_I-1-1",
        help="Path to the interactive scenario"
    )
    parser.add_argument(
        "-s", "--solution", type=str,
        default="../example_scenarios/solution/KS1:SA1:DEU_A9-2_1_T-1:2018b.xml",
        help="Path to the CommonRoad solution file"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="../example_scenarios/gif", help="Output folder path",
    )
    parser.add_argument(
        "-v", "--video", action="store_true", default=False, help="Create video",
    )
    parser.add_argument(
        "-sm", "--sumo_manager", action="store_true", default=False, help="Using the sumo-manager",
    )
    return parser


def simulate_interactive_solution(interactive_scenario_folder: str,
                                  solution_file: str,
                                  output_folder_path: str = None,
                                  creating_video: bool = False,
                                  use_sumo_manager: bool = False) -> Tuple[Scenario, Scenario]:
    """
    Simulate an interactive scenario with a solution trajectory
    :param interactive_scenario_folder: The path to the interactive scenario
    :param solution_file: The path to the solution file
    :param output_folder_path: The path to the output folder path for the videos
    :param creating_video: Indicates whether to create video or not
    :param use_sumo_manager: Indicates whether to use the SUMO-Manager or not
    :return: Tuple of the intact and with ego simulated scenarios
    """
    with open(os.path.join(interactive_scenario_folder, "simulation_config.p"), "rb") as input_file:
        conf = pickle.load(input_file)

    scenario_file = os.path.join(interactive_scenario_folder, f"{conf.scenario_name}.cr.xml")
    scenario, planning_problem_set = CommonRoadFileReader(scenario_file).open()

    scenario_wrapper = AbstractScenarioWrapper()
    scenario_wrapper.sumo_cfg_file = os.path.join(interactive_scenario_folder,
                                                  f"{conf.scenario_name}.sumo.cfg")
    scenario_wrapper.lanelet_network = scenario.lanelet_network

    solution = CommonRoadSolutionReader.open(solution_file)

    # Simulate with ego
    simulated_scenario_with_ego = simulate_scenario(conf,
                                                    scenario_wrapper,
                                                    interactive_scenario_folder,
                                                    num_of_steps=conf.simulation_steps,
                                                    planning_problem_set=planning_problem_set,
                                                    solution=solution,
                                                    use_sumo_manager=use_sumo_manager)
    simulated_scenario_with_ego.scenario_id = scenario.scenario_id

    # Simulate without ego
    simulated_scenario_without_ego = simulate_scenario(conf,
                                                       scenario_wrapper,
                                                       interactive_scenario_folder,
                                                       num_of_steps=conf.simulation_steps,
                                                       planning_problem_set=planning_problem_set,
                                                       solution=None,
                                                       use_sumo_manager=use_sumo_manager)
    simulated_scenario_without_ego.scenario_id = scenario.scenario_id

    if creating_video:
        if output_folder_path is None:
            output_folder_path = os.path.dirname(solution_file)
        for idx, planning_problem in enumerate(planning_problem_set.planning_problem_dict.values()):
            create_video(simulated_scenario_with_ego, output_folder_path, follow_ego=True)

    return simulated_scenario_without_ego, simulated_scenario_with_ego


if __name__ == '__main__':
    # prepare required arguments
    interactive_scenario_folder = "../example_scenarios/interactive/USA_US101-7_3_I-1-1"
    solution_file = "../example_scenarios/solution/KS2:SM1:USA_US101-7_3_T-1:2020a.xml"
    output_folder_path = "../example_scenarios/gif"
    creating_video = True
    use_sumo_manager = False

    # simulate the interactive scenario
    without_ego, with_ego = simulate_interactive_solution(interactive_scenario_folder=interactive_scenario_folder,
                                                          solution_file=solution_file,
                                                          output_folder_path=output_folder_path,
                                                          creating_video=creating_video,
                                                          use_sumo_manager=use_sumo_manager)
