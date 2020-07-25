""""
Adapted from main script to generate sumo scenarios and convert them to interactive cr scenarios for existing cr maps.
"""
import logging
import traceback
import random

import matplotlib as mpl
from pathlib import Path
import os
from commonroad.visualization.video import create_scenario_video

from scenario_generation.scenario_util import init_logging

mpl.use('TkAgg')
import os
from pathlib import Path

from crmapconverter.sumo_map.cr2sumo import CR2SumoMapConverter
from scenario_generation.interactive_scenarios_genaration import GenerateCRScenarios_I
from sumo2cr.interface.sumo_simulation import SumoSimulation
from sumo2cr.maps.util import *
from sumo2cr.maps.sumo_scenario import ScenarioWrapper
import shutil
import time

# Options
scenario_directory = '/home/yueming/cr_map'
output_folder = '/home/yueming/Scenarios_test'
CREATE_VIDEO = 0 #True

# load parameters
from scenario_generation.config_files.scenario_config import ScenarioConfig
from scenario_generation.config_files.sumo_config import SumoConf
from scenario_generation.config_files.cr2sumo_map_config import CR2SumoNetConfig_edited
# use vehicle parameters from sumo_config
sumo_conf = SumoConf()
cr2net_conf = CR2SumoNetConfig_edited()
cr2net_conf.veh_params = sumo_conf.veh_params

scenario_config = ScenarioConfig()

max_scenario_number = 0
obtained_scenario_number = 0
filenames = list(Path(scenario_directory).rglob("*.xml"))
random.shuffle(filenames)
timestr = time.strftime("%Y%m%d-%H%M%S")

# start logging, choose logging levels logging.INFO, logging.CRITICAL, logging.DEBUG
logger = init_logging(__name__, logging.INFO)

for cr_file in filenames:
    cr_file = str(cr_file)
    logger.info(f'Start with map {cr_file}')
    if '.net' in cr_file:
        continue

    # create unique scenario ids for each scenario
    max_scenario_number += scenario_config.scen_per_map
    split_map_name = os.path.splitext(os.path.basename(cr_file))[0].replace('_', '-').rsplit('-')
    if split_map_name[0] == 'C':
        del split_map_name[0]
    location_name = split_map_name[0] + '_' + split_map_name[1]
    orig_map_name = location_name + '-' + split_map_name[2]
    scenario_config.map_name = location_name

    dir_name = os.path.join(output_folder, timestr, orig_map_name)
    os.makedirs(dir_name, exist_ok=True)

    map_nr = int(split_map_name[2])

    try:
        # conversion from CommonRoad to SUMO map
        sumo_net_path = dir_name + "/" + location_name + '-' + str(map_nr) + ".net.xml"
        cr2sumo_converter = CR2SumoMapConverter.from_file(cr_file, cr2net_conf)
        cr2sumo_converter._convert_map()
        cr2sumo_converter.write_intermediate_files(sumo_net_path)
        logger.info(f'write map to path {cr_file}')
        conversion_possible = cr2sumo_converter.merge_intermediate_files(sumo_net_path, cleanup=False)

        if not conversion_possible:
            logger.warning('Conversion to net file failed!')
            continue

        # read boundary from netfile
        while os.path.exists(sumo_net_path) == False:
            time.sleep(0.05)

        scenario_counter = 0
        for j in range(scenario_config.scen_per_map):
            scenario_name = location_name + '-' + str(map_nr) + "_" + str(j + 1) + "_I"
            sumo_conf.scenario_name = scenario_name
            sumo_conf.scenarios_path = dir_name

            scenario_dir_name = os.path.join(dir_name, scenario_name)
            if os.path.exists(scenario_dir_name) == False:
                os.mkdir(scenario_dir_name)
            sumo_net_copy = os.path.join(scenario_dir_name, scenario_name + ".net.xml")
            cr_map_copy = os.path.join(scenario_dir_name, scenario_name + ".cr.xml")
            shutil.copy(sumo_net_path, sumo_net_copy)
            shutil.copy(cr_file, cr_map_copy)

            # generate route file and additional files for SUMO simulation
            scenario_wrapper = ScenarioWrapper.init_from_net_file(net_file=sumo_net_copy,
                                                                  cr_map_path=cr_file,
                                                                  conf=sumo_conf)
            # simulate sumo scenario and extract scenario files
            sumo_sim = SumoSimulation()
            sumo_sim.initialize(sumo_conf, scenario_wrapper=scenario_wrapper)

            for step in range(sumo_conf.simulation_steps):
                sumo_sim.simulate_step()

            sumo_sim.stop()
            scenario = sumo_sim.commonroad_scenarios_all_time_steps()

            ###########################################
            # get mappings between vehicle ids in sumo and cr
            vehicle_ids_cr2sumo = sumo_sim.ids_cr2sumo
            #vehicle_ids_sumo2cr = sumo_sim.ids_sumo2cr
            ###########################################

            # select ego vehicles for planning problems and postprocess final CommonRoad scenarios
            cr_scenarios = GenerateCRScenarios_I(scenario, sumo_conf.simulation_steps, sumo_conf.scenario_name,
                                               scenario_config, scenario_dir_name)

            cr_scenarios.create_cr_scenarios(delete_collising_obstacles=True)

            ego_ids_cr = cr_scenarios.ego_id_list

            scenario_nr_new = cr_scenarios.write_cr_file_and_video(map_nr, scenario_counter, CREATE_VIDEO,
                                                                   check_validity=False)
            ###############################################
            # write ego vehicle id to sumo route file
            ego_ids = []
            #for ego_id in ego_ids_cr:
                #ego_ids.append(vehicle_ids_cr2sumo['all_ids'][ego_id])
            ego_ids.append(vehicle_ids_cr2sumo['all_ids'][ego_ids_cr[0]])
            rou_file_names = list(Path(scenario_dir_name).rglob("*.rou.xml"))
            rou_file = str(rou_file_names[0])
            write_ego_ids_to_rou_file(rou_file, ego_ids)
            ###############################################

            scenario_counter += scenario_nr_new
            obtained_scenario_number += scenario_nr_new
    except BaseException as e:
        logger.warning(f'UNEXPECTED ERROR, continue with next scenario: {traceback.format_exc()}')

logger.info(f'max_scenario_number: {max_scenario_number}, obtained_scenario_number: {obtained_scenario_number}')
