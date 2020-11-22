""""
Script which converts a static CommonRoad scenario with interactive SUMO scenario,
where the vehicles are initialized exactly as in the static scenario
"""
import argparse
import pickle
import sys
from typing import Tuple

import matplotlib as mpl
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.scenario.scenario import ScenarioID, Scenario

from configuration import CONFIG_TYPE, get_interactive_scenario_configuration
from configuration import SumoConfigBase

mpl.use('TkAgg')

from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter
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
        "-cr", "--cr_scneario", type=str,
        default="./example_scenarios/cr_scenario/DEU_A9-2_1_T-1.xml",
        help="Path to the CommonRoad scenario to be converted"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="./example_scenarios/output", help="Output folder path",
    )
    parser.add_argument(
        "-v", "--video", action="store_true", default=False, help="Create video",
    )
    parser.add_argument(
        "-c", "--config", type=CONFIG_TYPE, default=CONFIG_TYPE.SUMO_CONFIG_1,
        choices=list(CONFIG_TYPE),
        help="Configuration type of the simulation"
    )
    return parser


def reduce_scenario(scenario: Scenario):
    """
    Reduces a scenario from static interactive by dropping all the obstacle states except the first
    :param scenario: The scenario to reduce
    """
    for obstacle in scenario.dynamic_obstacles:
        obstacle.prediction.trajectory.state_list = [obstacle.prediction.trajectory.state_list[0]]


def convert_to_sumo_files(scenario_file: str,
                          output_folder: str,
                          conf: SumoConfigBase) -> CR2SumoMapConverter or None:
    """
    Convert a static scenario to SUMO files
    :param scenario_file: The path to the static CommonRoad scenario
    :param output_folder: The path to the output folder
    :param conf: The configuration used by the SUMO files
    :return: Converter object if the conversion was successful
    """
    # Generate network file
    os.makedirs(output_folder, exist_ok=True)

    # load CR scenario and translate to origo
    scenario, planning_problem_set = CommonRoadFileReader(scenario_file).open()
    # translate_scenario(scenario, planning_problem_set)

    # convert scenario to SUMO files
    converter = CR2SumoMapConverter(scenario.lanelet_network, conf)
    converter.scenario_name = conf.scenario_name
    print(f'Write SUMO files for {scenario_file}')
    conversion_possible = converter.convert_scenario_to_net_file(scenario, output_folder)

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
        pickle.dump(conf, f)

    return converter


def convert_scenario(cr_scenario_path: str,
                     output_folder_path: str,
                     config_type: CONFIG_TYPE,
                     creating_video: bool = False) -> Tuple[bool, str]:
    """
    Convert a static CommonRoad scenario to interactive
    :param cr_scenario_path: The path to the static CommonRoad scenario
    :param output_folder_path: The path to the output folder
    :param config_type: The type of the configuration, which will be used by SUMO
    :param creating_video: Indicates whether to create vieo or not
    :return: Indicator of successful conversion and the path to the converted interactive scenario
    """
    if creating_video:
        raise NotImplementedError()

    benchmark_id = ScenarioID.from_benchmark_id(
        os.path.splitext(os.path.basename(cr_scenario_path))[0],
        scenario_version="2020a")
    benchmark_id.prediction_type = 'I'

    conf = get_interactive_scenario_configuration(config_type, str(benchmark_id))
    output_folder = os.path.join(output_folder_path, conf.scenario_name)

    scenario_wrapper = convert_to_sumo_files(cr_scenario_path, output_folder, conf)
    return scenario_wrapper is not None, output_folder


if __name__ == '__main__':
    arguments = convert_scenario_argsparser().parse_args(sys.argv[1:])
    convert_scenario(cr_scenario_path=arguments.cr_scneario,
                     output_folder_path=arguments.output,
                     config_type=arguments.config,
                     creating_video=arguments.video)
