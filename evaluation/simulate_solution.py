import os
from copy import deepcopy
import matplotlib

matplotlib.use('TkAgg')
from commonroad.scenario.scenario import Scenario
from cr2sumo.interface.sumo_interface import SumoInterface
from cr2sumo.rpc.sumo_client import SumoRPCClient
from cr2sumo.visualization.video import create_video
from sumo_config.default import SumoCommonRoadConfig
from commonroad.common.solution import CommonRoadSolutionReader as sr

class simulation_solution:
    scenario: Scenario              #for storing the complete scenario in the end
    conf: SumoCommonRoadConfig      #to keep possibility to rerun
    ego_showup = -1                 #default for recognizing
    solution = None


    def __init__(self, scenario_name: str, visualize: bool):
        #startup to simulate the scenario (from simualte_scenario)
        scenario_folder: str = os.path.join(os.getcwd(), "scenarios", scenario_name)
        print('Simulating {}'.format(scenario_name))

        conf = SumoCommonRoadConfig()
        conf.scenario_name = scenario_name
        self.conf = conf

        sumo_interface = SumoInterface()
        sumo_client: SumoRPCClient = sumo_interface.start_simulator()
        solution_path = os.path.join(scenario_folder, conf.scenario_name + 'solution'+'.xml')
        self.solution = sr.open(solution_path)
        sumo_client.send_sumo_scenario(self.conf.scenario_name, scenario_folder)
        sumo_client.initialize(self.conf)

        #for loop iterating through all time steps
        i = 0           #numer of time step the ego vehicle is currently in

        for t in range(500):
            ego_vehicles = sumo_client.ego_vehicles
            if len(ego_vehicles) > 0:
                if self.ego_showup ==-1:
                    self.ego_showup=sumo_client.current_time_step
                for id, ego_vehicle in ego_vehicles.items():
                    ego_trajectory = self.solution.planning_problem_solutions[0].trajectory  #only one ego vehicle as i could not test with more ego vehicles
                    if len(ego_trajectory.state_list)>i:
                        state = deepcopy(ego_trajectory.state_list[i])
                        state.time_step = 1
                        ego_vehicle.set_planned_trajectory([state])                         #seting planned trajectory

                i = i +1
            if i == len(self.solution.planning_problem_solutions[0].trajectory.state_list)+1:   #end of solution
                break
            sumo_client.send_ego_vehicles(ego_vehicles)
            sumo_client.simulate_step()


        self.scenario = sumo_client.commonroad_scenarios_all_time_steps()

        sumo_client.stop()
        # Create video and plot the simulation
        if visualize:
            output_folder = "./videos"
            os.makedirs(output_folder, exist_ok=True)
            print("Creating video")
            create_video(sumo_client, self.ego_showup, self.ego_showup+len(self.solution.planning_problem_solutions[0].trajectory.state_list), output_folder)
            print("Video created")

        sumo_interface.stop_simulator()

        #synchronization of scenario and solution time steps
        for other_vehicle in self.scenario.dynamic_obstacles:
            for state in other_vehicle.prediction.trajectory.state_list:
                state.time_step = state.time_step-self.ego_showup

        #removing states and vehicles before the ego vehicle shows up
        for other_vehicle in self.scenario.dynamic_obstacles:
            while len(other_vehicle.prediction.trajectory.state_list) > 0 and other_vehicle.prediction.trajectory.state_list[0].time_step < 0:
                del other_vehicle.prediction.trajectory.state_list[0]
            if len(other_vehicle.prediction.trajectory.state_list)<1:
                self.scenario.remove_obstacle(other_vehicle)



#s = simulation_solution('DEU_Muehlhausen-13_1_I',False)
#print(cf.ClosestDistance.evaluate(s.scenario, None, s.solution.planning_problem_solutions[0].trajectory))
#print(cf.Evaluation.Position(s.scenario, s.scenario, [s.solution.planning_problem_solutions[0].trajectory]))


