"""
Check the determinism of example_scenarios by resimulation
"""
import copy
from copy import deepcopy
import os
from typing import List

from commonroad.scenario.trajectory import State, Trajectory
from commonroad.scenario.scenario import Scenario, LaneletNetwork
from commonroad.scenario.obstacle import DynamicObstacle

import os
import matplotlib
matplotlib.use('TkAgg')
from cr2sumo.interface.sumo_interface import SumoInterface
from cr2sumo.rpc.sumo_client import SumoRPCClient
from sumo_config.default import SumoCommonRoadConfig


def get_variable_lists(obstacle: DynamicObstacle):
    '''
    get variables needed for the test from scenarioa
    '''
    state_list = obstacle.prediction.trajectory.state_list
    accel_list = []
    velocity_list = []
    position_x_list = []
    position_y_list = []
    orientation_list = []
    for state in state_list:
        accel_list.append(state.acceleration)
        velocity_list.append(state.velocity)
        position_x_list.append(state.position[0])
        position_y_list.append(state.position[1])
        orientation_list.append(state.orientation)
    variable_lists = {'accel': accel_list, 'v': velocity_list, "pos_x": position_x_list, 'pos_y': position_y_list, 'orientation': orientation_list}
    #variable_lists = {"pos_x": position_x_list, 'pos_y': position_y_list,
    #                  'orientation': orientation_list}
    return variable_lists


def if_equal(list1: List[float], list2: List[float], allowed_error=1) -> bool:
    '''
    compare two lists of 'float' --> almost equal
    '''
    equal = True
    len1 = len(list1)
    len2 = len(list2)
    if len1 != len2:
        equal = False
        print("Error: lists' lengths don't match")
    else:
        for i in range(len1):
            if abs(list1[i] - list2[i]) > allowed_error:
                equal = False
                break
    return equal


def check_determinism(scenario_name: str, scenario_folder: str=os.path.join(os.getcwd(), "example_scenarios", "DEU_Muehlhausen-13_2_I")) -> bool:
    """
    Check if a scenario is deterministic by resimulting scenario through SUMO.
    :param scenario_name: The name of the scenario to be simulated
    :param scenario_folder: The folder where the sumo files can be found
    """
    
    print('Simulating {}'.format(scenario_name))
    conf = SumoCommonRoadConfig()
    conf.scenario_name = scenario_name
    conf.presimulation_steps = 200
    
    # Create Interface to SUMO
    sumo_interface = SumoInterface()
    
    ##
    ## SIMULATION multiple times
    ##
    list_simulated_scenario = []
    simulation_times = 2  # option
    deterministic = True
    
    for i in range(simulation_times):
        sumo_client: SumoRPCClient = sumo_interface.start_simulator()
        # folder = 'path_to_sumo_files'
        # upload folder contains all files needed for sumo-simulation
        sumo_client.send_sumo_scenario(conf.scenario_name, scenario_folder)
        sumo_client.initialize(conf)

        #Simulate through all time steps
        for t in range(200):
            ego_vehicles = sumo_client.ego_vehicles
            print(t, 'FOUND', len(ego_vehicles), 'EGO VEHILES')
            time_step = sumo_client.current_time_step
            commonroad_scenario: Scenario = sumo_client.commonroad_scenario_at_time_step(time_step)

            # # plan trajectories for all ego vehicles
            for id, ego_vehicle in ego_vehicles.items():
                current_state = ego_vehicle.current_state
                state = deepcopy(current_state)
                state.time_step = 1
                ego_trajectory = [state]
                ego_vehicle.set_planned_trajectory(ego_trajectory)

            sumo_client.send_ego_vehicles(ego_vehicles)
            sumo_client.simulate_step()
        #Record the simulated scenario
        commonroad_scenario: Scenario = sumo_client.commonroad_scenarios_all_time_steps()
        list_simulated_scenario.append(commonroad_scenario)
        sumo_client.stop()
     
    sumo_interface.stop_simulator()
    print('Simulation {} ended'.format(scenario_name))

    # compare the simulated example_scenarios
    list_copy = copy.deepcopy(list_simulated_scenario)
    for idx in range(len(list_simulated_scenario) - 1):
        scenario_test = list_simulated_scenario[idx]
        del list_copy[idx]
        for scenario in list_copy:
            for obs_test_id, obs_test in scenario_test._dynamic_obstacles.items():
                variable_lists_test = get_variable_lists(obs_test)
                variable_lists = get_variable_lists(scenario._dynamic_obstacles[obs_test_id])
                # use almost equal
                for key in variable_lists.keys():
                    if not if_equal(variable_lists[key], variable_lists_test[key]):
                        print("This scenario is not deterministic.")
                        deterministic = False
                        break
                break
            break

    if deterministic:
        print("This scenario is deterministic.")

    return deterministic


# Test run
deterministic = check_determinism('DEU_Muehlhausen-13_1_I')
