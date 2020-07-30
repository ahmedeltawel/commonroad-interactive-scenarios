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
from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblemSet, PlanningProblem
from commonroad.scenario.trajectory import State

class simulation_solution:
    scenario: Scenario              #for storing the complete scenario in the end
    conf: SumoCommonRoadConfig      #to keep possibility to rerun


    def __init__(self, scenario_name: str, config):
        #startup to simulate the scenario (from simualte_scenario)
        scenario_folder: str = os.path.join(os.getcwd(), "scenarios", scenario_name)
        print('Simulating {}'.format(scenario_name))
        if config is None:
            conf = SumoCommonRoadConfig()
            conf.scenario_name = scenario_name
            self.conf = conf
            self.conf.simulation_steps = 500
        else:
            self.conf = config
        sumo_interface = SumoInterface()
        sumo_client: SumoRPCClient = sumo_interface.start_simulator()
        solution_path = os.path.join(scenario_folder, conf.scenario_name + 'solution'+'.xml')
        solution = sr.open(solution_path)
        sumo_client.send_sumo_scenario(self.conf.scenario_name, scenario_folder)
        sumo_client.initialize(self.conf)

         #for loop iterating through all time steps
        i = 0
        for t in range(self.conf.simulation_steps):
            ego_vehicles = sumo_client.ego_vehicles
            if len(ego_vehicles) > 0:
                print(sumo_client.current_time_step)
                for id, ego_vehicle in ego_vehicles.items():
                    ego_trajectory = solution.planning_problem_solutions[0].trajectory
                    if len(ego_trajectory.state_list)>i:
                        state = deepcopy(ego_trajectory.state_list[i])
                        state.time_step = 1
                        ego_vehicle.set_planned_trajectory([state])

                i = i +1
            if i == len(solution.planning_problem_solutions[0].trajectory.state_list)+1:
                break
            sumo_client.send_ego_vehicles(ego_vehicles)
            sumo_client.simulate_step()


        self.scenario = sumo_client.commonroad_scenarios_all_time_steps()
        sumo_client.stop()
        #sumo_interface.stop_simulator()

        output_folder = "./"
        print("Creating video")
        create_video(sumo_client, self.conf.video_start, self.conf.video_end, output_folder)
        print("Video created")
        #scenario = sumo_client.commonroad_scenarios_all_time_steps()
        plt.clf()
        draw_object(self.scenario)
        plt.autoscale()
        plt.axis('equal')
        print("Plotting scenario")
        plt.show()
        sumo_interface.stop_simulator()


s = simulation_solution('DEU_Muehlhausen-13_1_I', None)
#cf.ClosestDistance.evaluate(s.scenario,None, s.))

#s.visualize()
