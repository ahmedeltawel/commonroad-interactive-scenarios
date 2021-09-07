""""
Script which converts a static CommonRoad scenario with interactive SUMO scenario, where the vehicles are initialized exactly as in the static scenario
"""
import argparse
import glob
import pickle
import sys

import matplotlib as mpl

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.scenario.scenario import ScenarioID, Scenario
from crdesigner.conversion.sumo_map.config import SumoConfig
from simulation.simulations import simulate_with_planner

mpl.use('TkAgg')

from crdesigner.conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter
from sumocr.maps.util import *

# load parameters

__author__ = "Yueming Li, Peter Kocsis"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"


def convert_scenario_argsparser() -> argparse.ArgumentParser:
    """Returns a parser for the script's arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--in_path", type=str, default="./example_scenarios/cr_scenario/",
        help="Path to folder with the CommonRoad scenarios to be converted"
    )
    parser.add_argument(
        "-o", "--out_path", type=str, default="./example_scenarios/output", help="Output folder path",
    )
    return parser


def reduce_scenario(scenario: Scenario):
    for obstacle in scenario.dynamic_obstacles:
        obstacle.prediction.trajectory.state_list = [obstacle.prediction.trajectory.state_list[0]]


def convert_to_sumo_files(scenario_file: str,
                          output_folder_path: str,
                          conf: SumoConfig) -> CR2SumoMapConverter:

    # load CR scenario and translate to origo
    scenario, planning_problem_set = CommonRoadFileReader(scenario_file).open()
    conf.country_id = scenario.scenario_id.country_id
    scenario.scenario_id.obstacle_behavior = "I"
    conf.scenario_name = str(scenario.scenario_id)
    conf.presimulation_steps = 0
    output_folder = os.path.join(output_folder_path, conf.scenario_name)
    os.makedirs(output_folder, exist_ok=True)

    # convert scenario to SUMO files
    converter_config = SumoConfig()
    converter_config.scenario_name = str(scenario.scenario_id)
    converter_config.country_id = scenario.scenario_id.country_id
    converter = CR2SumoMapConverter(scenario, converter_config)
    converter.scenario_name = conf.scenario_name
    print(f'Write SUMO files for {scenario_file}')
    conversion_possible = converter.create_sumo_files(output_folder, traffic_from_trajectories=True)

    # save the reduced CR scenario
    reduce_scenario(scenario)
    scenario.scenario_id = conf.scenario_name
    CommonRoadFileWriter(scenario,
                         planning_problem_set,
                         author=scenario.author,
                         affiliation=scenario.affiliation,
                         source=scenario.source,
                         tags=scenario.tags,
                         location=scenario.location).write_to_file(
        os.path.join(
            output_folder,
            conf.scenario_name + ".cr.xml"),
        overwrite_existing_file=OverwriteExistingFile.ALWAYS)

    if not conversion_possible:
        print('Conversion to net file failed!')
        return None

    # Save the config
    with open(os.path.join(output_folder, "simulation_config.p"), 'wb') as f:
        goal_times = [state.time_step for pp_id, pp in planning_problem_set.planning_problem_dict.items()
                      for state in pp.goal.state_list if hasattr(state, "time_step")]
        if len(goal_times) > 0:
            conf.simulation_steps = max(goal_times, key=lambda time_interval: time_interval.end).end
            print(conf.simulation_steps)
        else:
            conf.simulation_steps = max(obs.prediction.final_time_step for obs in scenario.obstacles)

        pickle.dump(conf, f)

    return converter


def convert_scenario(cr_scenario_path: str,
                     output_folder_path: str,
                     conf=None) -> bool:
    """
    Generates interactive scenarios from CR maps
    :param cr_maps_folder_path: Path to the folder which contains the CR scenarios
    :param output_folder_path: Path of the output folder
    :param create_video: Indicates whether to create video about the new scenario or not
    :param num_max_resimulation: The number of maximum resimulation which is used in cases
    when no interesting ego vehicle has been found in the generated traffic
    :return Num of generated scenarios
    """

    scenario_wrapper = convert_to_sumo_files(cr_scenario_path, output_folder_path, conf)
    return scenario_wrapper is not None


if __name__ == '__main__':
    arguments = convert_scenario_argsparser().parse_args(sys.argv[1:])

    for scenario_file in glob.glob(os.path.join(arguments.in_path, "*.xml")):
        try:
            convert_scenario(cr_scenario_path=scenario_file,
                             output_folder_path=arguments.out_path,
                             conf=DefaultConfig())
        except:
            continue
