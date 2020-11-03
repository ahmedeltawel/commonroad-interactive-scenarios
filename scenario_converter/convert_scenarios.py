""""
Script which converts a static CommonRoad scenario with interactive SUMO scenario, where the vehicles are initialized exactly as in the static scenario
"""
import argparse
import sys
import time
import pickle

import matplotlib as mpl

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.scenario.scenario import ScenarioID, Scenario
from configuration import CONFIG_TYPE, get_interactive_scenario_configuration
from configuration import SumoConfigBase

mpl.use('TkAgg')

from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter
from sumocr.maps.util import *
import numpy as np

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
        "-cr", "--cr_scneario", type=str, default="./example_scenarios/cr_scenario/DEU_Ibbenbueren-7_1_T-1.xml",
        help="Path to the CommonRoad scenario to be converted"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="./example_scenarios/output", help="Output folder path",
    )
    parser.add_argument(
        "-v", "--video", action="store_true", default=False, help="Create video",
    )
    parser.add_argument(
        "-c", "--config", type=CONFIG_TYPE, default=CONFIG_TYPE.SUMO_CONFIG_1, choices=list(CONFIG_TYPE),
        help="Configuration type of the simulation"
    )
    parser.add_argument(
        "-sm", "--sumo_manager", action="store_true", default=False, help="Using the sumo-manager",
    )
    return parser


# def translate_scenario(scenario, planning_problem_set, position=np.array([0, 0])):
#     # translate scenario to center
#     centroid = np.mean(np.concatenate(
#         [l.center_vertices for l in scenario.lanelet_network.lanelets]),
#         axis=0)
#     scenario.translate_rotate(position - centroid, 0)
#     planning_problem_set.translate_rotate(position - centroid, 0)


def reduce_scenario(scenario: Scenario):
    for obstacle in scenario.dynamic_obstacles:
        obstacle.prediction.trajectory.state_list = [obstacle.prediction.trajectory.state_list[0]]


def convert_to_sumo_files(scenario_file: str,
                          output_folder: str,
                          conf: SumoConfigBase) -> CR2SumoMapConverter:
    # Generate network file
    os.makedirs(output_folder, exist_ok=True)

    # load CR scenario and translate to origo
    scenario, planning_problem_set = CommonRoadFileReader(scenario_file).open()
    # translate_scenario(scenario, planning_problem_set)

    # convert scenario to SUMO files
    converter = CR2SumoMapConverter(scenario.lanelet_network, conf)
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

    # Save the scenario_wrapper
    with open(os.path.join(output_folder, "scenario_wrapper.p"), 'wb') as f:
        pickle.dump(converter, f)

    return converter


def convert_to_sumo_files_with_sumo_manager(scenario_file: str,
                                           output_folder: str,
                                           conf: SumoConfigBase):
    raise NotImplementedError()


def convert_scenario(cr_scenario_path: str,
                     output_folder_path: str,
                     config_type: CONFIG_TYPE,
                     use_sumo_manager: bool = False,
                     creating_video: bool = False) -> bool:
    """
    Generates interactive scenarios from CR maps
    :param cr_maps_folder_path: Path to the folder which contains the CR scenarios
    :param output_folder_path: Path of the output folder
    :param create_video: Indicates whether to create video about the new scenario or not
    :param num_max_resimulation: The number of maximum resimulation which is used in cases
    when no interesting ego vehicle has been found in the generated traffic
    :return Num of generated scenarios
    """
    if creating_video:
        raise NotImplementedError()

    benchmark_id = ScenarioID.from_benchmark_id(os.path.splitext(os.path.basename(cr_scenario_path))[0],
                                                scenario_version="2020a")
    benchmark_id.prediction_type = 'I'

    if use_sumo_manager:
        raise NotImplementedError()

        # Create Interface to SUMO
        # sumo_interface = SumoInterface()
        #
        # create_video_function = create_video_sumo_manager
        # conf = SumoManagerCommonRoadConfig()
        #
        # # TODO: Currently, the sumo manager is built with an older version of the sumo-interface, therefore the results
        # #  of the simulations with and without sumo-manager won't match.
        # #  Check for differences when the sumo-manager is updated!
        #     simulator = sumo_interface.start_simulator()
        #
        #     # upload folder contains all files needed for sumo-simulation
        #     simulator.send_sumo_scenario(conf.scenario_name, scenario_file_path)
        #     simulator.initialize(conf)
        #     return simulator

    else:
        conf = get_interactive_scenario_configuration(config_type, str(benchmark_id))
        output_folder = os.path.join(output_folder_path, conf.scenario_name)

        scenario_wrapper = convert_to_sumo_files(cr_scenario_path, output_folder, conf)
    return scenario_wrapper is not None


if __name__ == '__main__':
    arguments = convert_scenario_argsparser().parse_args(sys.argv[1:])
    convert_scenario(cr_scenario_path=arguments.cr_scneario,
                     output_folder_path=arguments.output,
                     config_type=arguments.config,
                     use_sumo_manager=arguments.sumo_manager,
                     creating_video=arguments.video)
