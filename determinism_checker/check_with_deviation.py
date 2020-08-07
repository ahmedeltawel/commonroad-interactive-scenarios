"""
Check the determinism of scenarios by calculating the deviations
"""
import os
from sumo2cr.interface.sumo_simulation import SumoSimulation
from sumo2cr.maps.sumo_scenario import ScenarioWrapper
from sumo_config.default import SumoCommonRoadConfig
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


conf = SumoCommonRoadConfig()
conf.scenario_name = 'DEU_Muehlhausen-1_1_I'  # given scenario name
scenario_folder = os.path.join(os.path.dirname(__file__),'../scenarios')
scenario_file = os.path.join(scenario_folder, conf.scenario_name)  # path to scenario files

list_simulated_scenario = []  # store simulated scenarios for every simulation
simulation_times = 10 # simulation times, option
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
# check determinism by calculating deviation of accelerates, velocities, positions and orientations
###
deterministic = True

for test_param in ['accel', 'v', 'pos_x', 'pos_y', 'orientation']:
    list_param = []
    vehicle_id_list = []
    for scenario in list_simulated_scenario:
        param_list = {}
        for obs_test_id, obs_test in scenario._dynamic_obstacles.items():
            param = get_variable_lists(obs_test)[test_param]
            param_list.update({str(obs_test_id): param})
            vehicle_id_list.append(obs_test_id)
        list_param.append(param_list)

    # vehicle_id_test = random.choice(vehicle_id_list)  # choose an arbitrary vehicle id
    vehicle_id_test = 314  # set an interesting vehicle id manually
    new_list = []
    for l in range(len(list_param[0][str(vehicle_id_test)]) - 1):
        new = []
        for n in range(simulation_times):
            new.append(list_param[n][str(vehicle_id_test)][l])
        new_list.append(new)
    dev_list = []
    for item in new_list:
        dev = 0
        mean = sum(item)/simulation_times
        for idx in range(simulation_times):
            dev += ((item[idx] - mean)**2)/simulation_times
        dev_list.append(dev)
    dev_final = sum(dev_list)/len(dev_list)
    print('Deviation of ' + test_param + ' is')
    print(dev_final)
    if dev_final > 0.05:
        deterministic = False
        break

if deterministic:
    print("This scenario is deterministic.")
else:
    print("This scenario is not deterministic.")


