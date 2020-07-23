import os
from copy import deepcopy
import matplotlib
import numpy as np
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from commonroad.visualization.draw_dispatch_cr import draw_object
from commonroad.scenario.scenario import Scenario
from cr2sumo.interface.sumo_interface import SumoInterface
from cr2sumo.rpc.sumo_client import SumoRPCClient
from cr2sumo.visualization.video import create_video
from sumo_config.default import SumoCommonRoadConfig
import submissions_models_cost_function as cf
from commonroad.common.solution import CommonRoadSolutionReader as sr

class simulation_solution:
    scenario: Scenario              #for storing the complete scenario in the end
    conf: SumoCommonRoadConfig      #to keep possibility to rerun


    def __init__(self, scenario_name: str):
        #startup to simulate the scenario (from simualte_scenario)
        scenario_folder: str = os.path.join(os.getcwd(), "scenarios", "cr_scenarios")
        print('Simulating {}'.format(scenario_name))
        conf = SumoCommonRoadConfig()
        conf.scenario_name = scenario_name
        self.conf = conf
        sumo_interface = SumoInterface()
        sumo_client: SumoRPCClient = sumo_interface.start_simulator()
        cr_file = os.path.join(scenario_folder, conf.scenario_name + '.xml')
        solution_path = os.path.join(scenario_folder, conf.scenario_name + 'solution'+'.xml')
        solution = sr.open(solution_path)
        sumo_client.send_commonroad_scenario(conf.scenario_name, cr_file)
        sumo_client.initialize(conf)


         #for loop iterating through all time steps
        for t in range(conf.simulation_steps):
            ego_vehicles = sumo_client.ego_vehicles
            for id, ego_vehicle in ego_vehicles.items():
                current_state = ego_vehicle.current_state
                state = deepcopy(current_state)
                state.time_step = 1
                ego_trajectory = solution.planning_problem_solutions[ego_vehicles.items().index(ego_vehicle)].trajectory
                ego_vehicle.set_planned_trajectory(ego_trajectory)

            sumo_client.simulate_step()

        self.scenario = sumo_client.commonroad_scenarios_all_time_steps()
        sumo_client.stop()
        sumo_interface.stop_simulator()


    def visualize(self):
        #to do, as resimualating is necessary at the moment
        sumo_interface = SumoInterface()
        sumo_client: SumoRPCClient = sumo_interface.start_simulator()
        cr_file = os.path.join(os.path.join(os.getcwd(), "scenarios", "cr_scenarios"), self.conf.scenario_name + '.xml')
        sumo_client.send_commonroad_scenario(self.conf.scenario_name, cr_file)
        sumo_client.initialize(self.conf)

        for t in range(self.conf.simulation_steps):
            ego_vehicles = sumo_client.ego_vehicles

            # plan trajectories for all ego vehicles
            for id, ego_vehicle in ego_vehicles.items():
                current_state = ego_vehicle.current_state
                state = deepcopy(current_state)
                state.time_step = 1
                ego_trajectory = [state]
                ego_vehicle.set_planned_trajectory(ego_trajectory)

            sumo_client.simulate_step()
        sumo_client.stop()
        # Create video and plot the simulation
        output_folder = "./"
        print("Creating video")
        create_video(sumo_client, self.conf.video_start, self.conf.video_end, output_folder)
        print("Video created")
        scenario = sumo_client.commonroad_scenarios_all_time_steps()
        plt.clf()
        draw_object(scenario)
        plt.autoscale()
        plt.axis('equal')
        print("Plotting scenario")
        plt.show()
        sumo_interface.stop_simulator()

s = simulation_solution('USA')
print(cf.AvgSpeed.evaluate(s.scenario,None, None))

#s.visualize()
