""""
Script to simulate interactive scenarios with solution trajectory to the planning problem
"""
__author__ = "Peter Kocsis"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.3"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"

import argparse
import os
import pickle
from typing import Tuple, Union

import matplotlib as mpl

mpl.use('TkAgg')

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.solution import CommonRoadSolutionReader
from commonroad.scenario.scenario import Scenario, Tag
from commonroad.planning.planning_problem import PlanningProblemSet

from simulation import simulate_scenario
from sumocr.maps.scenario_wrapper import AbstractScenarioWrapper
from sumocr.visualization.gif import create_gif

# import necessary classes from different modules
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.file_writer import OverwriteExistingFile


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


def simulate_with_solution(interactive_scenario_path: str,
                           solution_file: str = None,
                           output_folder_path: str = None,
                           create_GIF: bool = False,
                           use_sumo_manager: bool = False) \
        -> Tuple[Scenario, Union[Scenario, None], PlanningProblemSet]:
    """
    Simulate an interactive scenario with a solution trajectory
    
    :param interactive_scenario_path: path to the interactive scenario
    :param solution_file: path to the solution file
    :param output_folder_path: path to the output folder path for the videos
    :param create_GIF: indicates whether to create GIFs of the simulated scenario
    :param use_sumo_manager: indicates whether to use the SUMO-Manager
    :return: Tuple of the intact and with ego simulated scenarios
    """
    with open(os.path.join(interactive_scenario_path, "simulation_config.p"), "rb") as input_file:
        conf = pickle.load(input_file)

    scenario_file = os.path.join(interactive_scenario_path, f"{conf.scenario_name}.cr.xml")
    scenario, planning_problem_set = CommonRoadFileReader(scenario_file).open()

    scenario_wrapper = AbstractScenarioWrapper()
    scenario_wrapper.sumo_cfg_file = os.path.join(interactive_scenario_path, f"{conf.scenario_name}.sumo.cfg")
    scenario_wrapper.lanelet_network = scenario.lanelet_network

    # simulation without ego vehicle
    simulated_scenario_without_ego = simulate_scenario(conf,
                                                       scenario_wrapper,
                                                       interactive_scenario_path,
                                                       num_of_steps=conf.simulation_steps,
                                                       planning_problem_set=planning_problem_set,
                                                       solution=None,
                                                       use_sumo_manager=use_sumo_manager)
    simulated_scenario_without_ego.scenario_id = scenario.scenario_id

    # simulation with ego vehicle
    if solution_file:
        solution = CommonRoadSolutionReader.open(solution_file)

        simulated_scenario_with_ego = simulate_scenario(conf,
                                                        scenario_wrapper,
                                                        interactive_scenario_path,
                                                        num_of_steps=conf.simulation_steps,
                                                        planning_problem_set=planning_problem_set,
                                                        solution=solution,
                                                        use_sumo_manager=use_sumo_manager)
        simulated_scenario_with_ego.scenario_id = scenario.scenario_id

        if create_GIF:
            if not output_folder_path:
                output_folder_path = os.path.dirname(solution_file)

            for idx, planning_problem in enumerate(planning_problem_set.planning_problem_dict.values()):
                create_gif(simulated_scenario_with_ego, output_folder_path,
                           planning_problem=planning_problem,
                           trajectory=solution.planning_problem_solutions[idx].trajectory,
                           secondary_scenario=simulated_scenario_without_ego,
                           follow_ego=True)

        return simulated_scenario_without_ego, simulated_scenario_with_ego, planning_problem_set
    else:
        print("No solution file given, skipping simulation with solution trajectory.")
        return simulated_scenario_without_ego, None, planning_problem_set


if __name__ == '__main__':
    # prepare required arguments
    name_scenario = "USA_US101-7_3_I-1-1"
    path_scenario = "../scenarios/interactive/" + name_scenario

    name_solution = "KS2:SM1:USA_US101-7_3_T-1:2020a"
    path_solution = "../scenarios/solutions/" + name_solution + ".xml"

    path_output = "../scenarios/gifs"

    # simulate interactive scenario with and without ego vehicle
    scenario_without_ego, scenario_with_ego, pps = simulate_with_solution(interactive_scenario_path=path_scenario,
                                                                          solution_file=path_solution,
                                                                          output_folder_path=path_output,
                                                                          create_GIF=True,
                                                                          use_sumo_manager=False)

    author = 'Max Mustermann'
    affiliation = 'Technical University of Munich, Germany'
    source = ''
    tags = {Tag.URBAN}
    path_scenarios_simulated = "../scenarios/simulated/"

    # write simulated scenarios to file
    # without ego
    fw = CommonRoadFileWriter(scenario_without_ego, pps, author, affiliation, source, tags)
    fw.write_to_file(f"{path_scenarios_simulated}{name_scenario}.xml", OverwriteExistingFile.ALWAYS)
    # with ego
    if scenario_with_ego:
        fw = CommonRoadFileWriter(scenario_with_ego, pps, author, affiliation, source, tags)
        fw.write_to_file(f"{path_scenarios_simulated}{name_scenario}_ego.xml", OverwriteExistingFile.ALWAYS)
