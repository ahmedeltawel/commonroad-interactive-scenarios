"""
Check the determinism of scenarios by comparing difference of state values
"""
import os
import copy
import matplotlib.pyplot as plt
from typing import List
import random

from commonroad.visualization.draw_dispatch_cr import draw_object
from commonroad.scenario.trajectory import State
from sumo2cr.interface.sumo_simulation import SumoSimulation
from sumo2cr.maps.sumo_scenario import ScenarioWrapper
from sumo_config.config_generation import SumoConf
from commonroad.scenario.scenario import Scenario, LaneletNetwork
from commonroad.scenario.obstacle import DynamicObstacle
from sumo2cr.visualization.video import create_video



def get_variable_lists(obstacle: DynamicObstacle):
    """
    get necessary variables from dynamic obstacle states
    """
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


def if_equal(list1: List[float], list2 : List[float], allowed_error = 0.5) -> bool:
    """
    compare 2 lists of float variables using almost equal
    :param allowed_error:
    """
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



conf = SumoConf()
conf.scenario_name = 'DEU_Muehlhausen-1_1_I'  # given scenario name
scenario_folder = os.path.join(os.path.dirname(__file__),'../scenarios')
scenario_file = os.path.join(scenario_folder, conf.scenario_name)  # path to scenario files

list_simulated_scenario = []  # store simulated scenarios for every simulation
simulation_times = 2  # simulation times, option
video_output_folder = '/home/yueming/Scenarios_test'  # output folder path


###
# Simulation and record
###
for i in range(simulation_times):
    print(i+1, "th simulation start.")
    sumo_sim = SumoSimulation()
    sumo_sim.initialize(conf)
    for step in range(conf.simulation_steps):
        sumo_sim.simulate_step()
    sumo_sim.stop()
    # record simulated scenarios
    simulated_scenario = sumo_sim.commonroad_scenarios_all_time_steps()
    list_simulated_scenario.append(simulated_scenario)
    # create videos
    #create_video(sumo_sim, conf.video_start, conf.video_end, video_output_folder)

###
# plot the trajectories of one vehicle in each scenario
###
list_position_x = []
list_position_y = []
vehicle_id_list = []
for scenario in list_simulated_scenario:
    position_x_list = {}
    position_y_list = {}
    for obs_test_id, obs_test in scenario._dynamic_obstacles.items():
        pos_x = get_variable_lists(obs_test)['pos_x']
        pos_y = get_variable_lists(obs_test)['pos_y']
        position_x_list.update({str(obs_test_id): pos_x})
        position_y_list.update({str(obs_test_id): pos_y})
        vehicle_id_list.append(obs_test_id)
    list_position_x.append(position_x_list)
    list_position_y.append(position_y_list)

# vehicle_id_test = random.choice(vehicle_id_list)  # choose an arbitrary vehicle id
vehicle_id_test = 314  # set an interesting vehicle id manually
for n in range(simulation_times):
    plt.figure(figsize=(10, 10))
    plt.title('Trajectory of vehicle ' + str(vehicle_id_test) + ' in ' + str(n+1) + 'th simulation', fontsize=12, color='k')
    draw_object(list_simulated_scenario[n], draw_params={'time_begin': -1, 'time_end': -1})
    plt.plot(list_position_x[n][str(vehicle_id_test)], list_position_y[n][str(vehicle_id_test)], color='b', marker='o',
             markersize=1, zorder=20, linewidth=0.5, label='Simulated')
    plt.gca().set_aspect('equal')
    plt.margins(0, 0)
    #plt.savefig(os.path.join(video_output_folder, conf.scenario_name + '_' + str(n+1) + '.png'), format='png', dpi=300)
    #print("Trajectory x of vehicle " + str(vehicle_id_test) + " at " + str(n+1) + "th simulation is:")
    #print(list_position_x[n][str(vehicle_id_test)])




###
# check determinism by comparing states of all vehicles between recorded scenarios
###
deterministic = True
list_copy = copy.deepcopy(list_simulated_scenario)
for idx in range(len(list_simulated_scenario) - 1):
    if not deterministic:
        break
    scenario_test = list_simulated_scenario[idx]
    del list_copy[idx]
    for scenario in list_copy:
        if not deterministic:
            break
        # check the num of vehicles in scenarios
        if len(scenario_test._dynamic_obstacles) != len(scenario._dynamic_obstacles):
            print("This scenario is not deterministic. Different num of obstacle vehicles detected.")
            deterministic = False
        for obs_test_id, obs_test in scenario_test._dynamic_obstacles.items():
            if not deterministic:
                break
            # compare states of every vehicles
            variable_lists_test = get_variable_lists(obs_test)
            variable_lists = get_variable_lists(scenario._dynamic_obstacles[obs_test_id])
            # use almost equal
            for key in variable_lists.keys():
                if not deterministic:
                    break
                if not if_equal(variable_lists[key], variable_lists_test[key]):
                    print("This scenario is not deterministic. State Error too large")
                    deterministic = False

if deterministic:
    print("This scenario is deterministic.")
