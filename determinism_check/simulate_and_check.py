"""
Check the determinism of cr scenarios
"""
import copy
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


##
##get variables needed for the test from scenarioa
##
def get_variable_lists(obstacle: DynamicObstacle):
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
    return variable_lists

##
##compare two lists of 'float' --> almost equal
##
def if_equal(list1: List[float], list2 : List[float], allowed_error = 1e-6) -> bool:
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
                continue
    return equal



def check_determinism(scenario_name: str, scenario_folder: str=os.path.join(os.getcwd(), "scenarios", "a9")) -> bool:
    """
    Check if a scenario is deterministic using SUMO.
    :param scenario_name: The name of the scenario to be simulated
    :param scenario_folder: The folder where the rou file can be found
    """
    
    print('Simulating {}'.format(scenario_name))
    conf = SumoCommonRoadConfig()
    conf.scenario_name = scenario_name
    
    # Create Interface to SUMO
    sumo_interface = SumoInterface()
    
    ##
    ## SIMULATION multiple times
    ##
    list_simulated_scenario = []
    simulation_times = 2
    deterministic = True
    
    for i in range(simulation_times):
        sumo_client: SumoRPCClient = sumo_interface.start_simulator()
        
        # upload folder contains all files needed for sumo-simulation
        sumo_client.send_sumo_scenario(conf.scenario_name, scenario_folder)
        sumo_client.initialize(conf)

        #Simulate through all time steps
        for t in range(conf.simulation_steps):
            sumo_client.simulate_step()
        commonroad_scenario: Scenario = sumo_client.commonroad_scenarios_all_time_steps()
        list_simulated_scenario.append(commonroad_scenario)
        sumo_client.stop()
     
    sumo_interface.stop_simulator()
    print('Simulation {} ended'.format(scenario_name))
     
    
    #compare the simulated scenarios
    list_copy = copy.deepcopy(list_simulated_scenario)
    for idx in range(len(list_simulated_scenario) - 1):
        scenario_test = list_simulated_scenario[idx]
        #list_copy = copy.deepcopy(list_simulated_scenario)
        del list_copy[idx]
        for scenario in list_copy:
            for obs_test_id, obs_test in scenario_test._dynamic_obstacles.items():
                variable_lists_test = get_variable_lists(obs_test)
                variable_lists = get_variable_lists(scenario._dynamic_obstacles[obs_test_id])
                #use almost equal
                for key in variable_lists.keys():
                    if not if_equal(variable_lists[key], variable_lists_test[key]):
                        print("This scenario is not deterministic.")
                        deterministic = False
                        continue
                    continue
                continue
            continue

                #if variable_lists != variable_lists_test:
                    #print("This scenario is not deterministic.")
                    #deterministic = False
                    #continue
    if deterministic:
        print("This scenario is deterministic.")
        
    return deterministic


deterministic = check_determinism('a9')
