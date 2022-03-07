""""
Script to generate new scenarios using SUMO
"""
import argparse
import copy
import logging
import random
import shutil
import sys
import time
import traceback
from pathlib import Path
from typing import Tuple

import matplotlib as mpl
from commonroad.scenario.scenario import ScenarioID
from crdesigner.map_conversion.sumo_map.cr2sumo.converter import CR2SumoMapConverter
from scenario_factory.config_files.cr2sumo_map_config import CR2SumoNetConfig_edited

from scenario_generation.config_files.cr2sumo_map_config import CR2SumoNetConfig_edited
# load parameters
from scenario_generation.config_files.scenario_config import ScenarioConfig
from scenario_generation.config_files.sumo_config import SumoConf
from scenario_generation.scenario_util import init_logging
from sumocr.interface.sumo_simulation import SumoSimulation
from sumocr.maps.sumo_scenario import ScenarioWrapper
from sumocr.maps.util import *

from scenario_generator.interactive_scenarios_generation import GenerateCRScenarios_Interactive

try:
    from commonroad_sumo_manager.crsumo.interface.sumo_interface import SumoInterface
    from commonroad_sumo_manager.crsumo.rpc.sumo_client import SumoRPCClient
except ImportError as exp:
    warnings.warn("CommonRoad-SUMO-Manager is not installed, the usage is not supported!")

mpl.use('TkAgg')

__author__ = "Yueming Li, Peter Kocsis"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"


def generate_scenarios_argsparser() -> argparse.ArgumentParser:
    """Returns a parser for the script's arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-crm", "--cr_maps", type=str, default="./example_scenarios/cr_scenario",
        help="Path to the folder of input maps as CommonRoad example_scenarios"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="./example_scenarios/output", help="Output folder path",
    )
    parser.add_argument(
        "-v", "--video", action="store_true", default=False, help="Create video",
    )
    parser.add_argument(
        "-sm", "--sumo_manager", action="store_true", default=False, help="Use SUMO-Manager",
    )
    parser.add_argument(
        "-nmr", "--num_max_resimulation", type=int, default=10,
        help="Maximum number of resimulation",
    )
    return parser


def simulate_scenario(sumo_conf: SumoConf,
                      scenario_wrapper: ScenarioWrapper,
                      scenario_config: ScenarioConfig,
                      scenario_dir_path: str,
                      use_sumo_manager: bool = False) \
        -> Tuple[GenerateCRScenarios_Interactive, dict]:
    """
    Simulates traffic for a scenario
    :param sumo_conf: The SUMO configuration for the traffic simulation
    :param scenario_wrapper: Object contains scenario-relevant information
    :param scenario_config: The configuration of the scenario generation
    :param scenario_dir_path: Path to the folder which contains the scenario
    :param use_sumo_manager: Indicates whether to use the SUMO-Manager or not
    :return CR scenario generator object and vehicle ID mapping between CR and SUMO
    """
    sumo_interface = None
    if use_sumo_manager:
        sumo_interface = SumoInterface(use_docker=False)
        sumo_sim = sumo_interface.start_simulator()

        sumo_sim.send_sumo_scenario(sumo_conf.scenario_name,
                                    scenario_dir_path)
    else:
        sumo_sim = SumoSimulation()

    sumo_sim.initialize(sumo_conf, scenario_wrapper)

    for step in range(sumo_conf.simulation_steps):
        sumo_sim.simulate_step()

    sumo_sim.stop()
    scenario = sumo_sim.commonroad_scenarios_all_time_steps()

    ###########################################
    # get mappings between vehicle ids in sumo and maps
    vehicle_ids_cr2sumo = sumo_sim.ids_cr2sumo
    # vehicle_ids_sumo2cr = sumo_sim.ids_sumo2cr
    ###########################################

    if use_sumo_manager:
        sumo_interface.stop_simulator()

    # select ego vehicles for planning problems and postprocess final CommonRoad example_scenarios
    cr_scenarios = GenerateCRScenarios_Interactive(scenario, sumo_conf.simulation_steps,
                                                   sumo_conf.scenario_name,
                                                   scenario_config, scenario_dir_path)

    cr_scenarios.create_cr_scenarios()

    return cr_scenarios, vehicle_ids_cr2sumo


def generate_scenarios(cr_maps_folder_path: str,
                       output_folder_path: str,
                       create_video: bool = False,
                       num_max_resimulation: int = 10,
                       use_sumo_manager: bool = False) -> int:
    """
    Generates interactive scenarios from CR maps
    :param cr_maps_folder_path: Path to the folder which contains the CR scenarios
    :param output_folder_path: Path of the output folder
    :param create_video: Indicates whether to create video about the new scenario or not
    :param num_max_resimulation: The number of maximum resimulation which is used in cases
    when no interesting ego vehicle has been found in the generated traffic
    :param use_sumo_manager: Indicates whether to use the SUMO-Manager or not
    :return Num of generated scenarios
    """
    # Use vehicle parameters from sumo_config
    sumo_conf = SumoConf()
    cr2net_conf = CR2SumoNetConfig_edited()
    cr2net_conf.veh_params = sumo_conf.veh_params

    scenario_config = ScenarioConfig()

    max_num_of_scenarios = 0
    obtained_num_of_scenarios = 0
    map_filenames = list(Path(cr_maps_folder_path).rglob("*.xml"))
    random.shuffle(map_filenames)
    timestr = time.strftime("%Y%m%d-%H%M%S")

    # start logging, choose logging levels logging.INFO, logging.CRITICAL, logging.DEBUG
    logger = init_logging(__name__, logging.INFO)

    for map_file in map_filenames:
        map_file = str(map_file)
        logger.info(f'Start with map {map_file}')
        if '.net' in map_file:
            logger.warning(f'Map {map_file} contains ".net", therefore step over')
            continue

        # create unique scenario ids for each scenario
        max_num_of_scenarios += scenario_config.scen_per_map
        benchmark_id = ScenarioID.from_benchmark_id(
            f"{os.path.splitext(os.path.basename(map_file))[0]}-0", scenario_version="2020a")
        location_name = benchmark_id.country_id + '_' + benchmark_id.map_name
        orig_map_name = location_name + '-' + str(benchmark_id.configuration_id)
        scenario_config.map_name = location_name

        dir_path = os.path.join(output_folder_path, timestr, orig_map_name)
        os.makedirs(dir_path, exist_ok=True)

        map_nr = int(benchmark_id.configuration_id)

        try:
            # conversion from CommonRoad to SUMO map
            sumo_net_path = os.path.join(dir_path, location_name + '-' + str(map_nr) + ".net.xml")
            cr2sumo_converter = CR2SumoMapConverter.from_file(map_file, cr2net_conf)
            cr2sumo_converter.create_sumo_files(dir_path)
            logger.info(f'write map to path {map_file}')
            conversion_possible = cr2sumo_converter.merge_intermediate_files(sumo_net_path,
                                                                             cleanup=False)

            if not conversion_possible:
                logger.warning('Conversion to net file failed!')
                continue

            # read boundary from netfile
            timeout_of_wait = 100
            time_counter = 0
            while not os.path.exists(sumo_net_path):
                time.sleep(0.1)
                time_counter += 1
                if time_counter > timeout_of_wait:
                    raise RuntimeError(f"Sumo net path {sumo_net_path} not found!")

            scenario_counter = 0
            for j in range(scenario_config.scen_per_map):
                new_benchmark_id = copy.deepcopy(benchmark_id)
                new_benchmark_id.prediction_type = 'I'
                sumo_conf.scenario_name = str(new_benchmark_id)
                sumo_conf.scenarios_path = dir_path

                scenario_dir_name = os.path.join(dir_path, str(new_benchmark_id))
                if os.path.exists(scenario_dir_name) == False:
                    os.mkdir(scenario_dir_name)
                sumo_net_copy = os.path.join(scenario_dir_name, str(new_benchmark_id) + ".net.xml")
                cr_map_copy = os.path.join(scenario_dir_name, str(new_benchmark_id) + ".cr.xml")
                shutil.copy(sumo_net_path, sumo_net_copy)
                shutil.copy(map_file, cr_map_copy)

                # generate route file and additional files for SUMO simulation
                scenario_wrapper = ScenarioWrapper.init_from_net_file(net_file=sumo_net_copy,
                                                                      cr_map_path=cr_map_copy,
                                                                      conf=sumo_conf)

                simulation_rem_num_of_trials = num_max_resimulation
                while simulation_rem_num_of_trials > 0:
                    simulation_rem_num_of_trials -= 1
                    cr_scenarios, vehicle_ids_cr2sumo = simulate_scenario(sumo_conf,
                                                                          scenario_wrapper,
                                                                          scenario_config,
                                                                          scenario_dir_name,
                                                                          use_sumo_manager=use_sumo_manager)
                    ego_ids_cr = cr_scenarios.ego_id_list
                    if len(ego_ids_cr) != 0:
                        break
                else:
                    raise RuntimeError(
                        "Couldn't generate traffic which contains interesting ego vehicles")

                scenario_nr_new = cr_scenarios.write_cr_file_and_video(map_nr, scenario_counter,
                                                                       create_video,
                                                                       check_validity=False)
                ###############################################
                # write ego vehicle id to sumo route file
                ego_ids = []
                ego_ids.append(vehicle_ids_cr2sumo['all_ids'][ego_ids_cr[0]])
                rou_file_names = list(Path(scenario_dir_name).rglob("*.rou.xml"))
                rou_file = str(rou_file_names[0])
                write_ego_ids_to_rou_file(rou_file, ego_ids)
                ###############################################

                scenario_counter += scenario_nr_new
                obtained_num_of_scenarios += scenario_nr_new
        except BaseException as e:
            logger.warning(
                f'UNEXPECTED ERROR, continue with next scenario: {traceback.format_exc()}')

    logger.info(
        f'max_num_of_scenarios: {max_num_of_scenarios}, obtained_num_of_scenarios: {obtained_num_of_scenarios}')
    return obtained_num_of_scenarios


if __name__ == '__main__':
    arguments = generate_scenarios_argsparser().parse_args(sys.argv[1:])
    generate_scenarios(cr_maps_folder_path=arguments.cr_maps,
                       output_folder_path=arguments.output,
                       create_video=arguments.video,
                       num_max_resimulation=arguments.num_max_resimulation,
                       use_sumo_manager=arguments.sumo_manager)
