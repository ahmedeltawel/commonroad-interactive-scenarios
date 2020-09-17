"""
This class inherits from the class GenerateCRScenarios
"""

import os
import warnings
from typing import List, Callable

from commonroad.common.util import Interval
from commonroad.geometry.shape import Rectangle
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblemSet, PlanningProblem
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.trajectory import State
from commonroad.visualization.video import create_scenario_video
from scenario_generation.config_files.scenario_config import ScenarioConfig
from scenario_generation.cr_scenario_generation import GenerateCRScenarios
from scenario_generation.scenario_checker import check_collision

try:
    from commonroad.common.file_writer import Tag
except NameError:
    # using commonroad-io < 2020.1
    Tag = None


class GenerateCRScenarios_Interactive(GenerateCRScenarios):
    """
    Class for generating interactive CommonRoad example_scenarios with only initial states of vehicles.
    """

    def __init__(self, scenario: Scenario,
                 scenario_length: int,
                 scenario_name: str,
                 config: ScenarioConfig,
                 scenario_folder: str,
                 timestr: str = None,
                 ego_selection_criteria: List[Callable] = None):
        """
        Initialize new object
        :param scenario: The scenario which lanelet network will be used
        :param scenario_length: The length of the scenario
        :param scenario_name: The benchmark ID of the scenario
        :param config: The config of the scenario generation
        :param scenario_folder: The folder which contains the scenario
        :param timestr: Time stamp which will be written in folder name for file tracking
        :param ego_selection_criteria: The list of criteria which will be used for ego selection. If one of the criteria
        meets then the obstacle will be marked as possible ego vehicle
        """
        super().__init__(scenario, scenario_length, scenario_name, config, scenario_folder, timestr,
                         ego_selection_criteria)
        self.scenario_name = self.scenario_name + "_I"

    # Overload the methods in class GenerateCRScenarios
    def create_planning_problem(self, obstacles, planning_pro_with_lanelet=False,
                                visualize_ego=False, planning_pro_per_scen=1):
        """
        Define planning problem for commonroad example_scenarios.
        :param obstacles: commonroad example_scenarios converted by _get_all_cr_obstacles
        :param planning_pro_with_lanelet: define goal area in the planning problem by state or lanelet.
        :param planning_pro_per_scen: number of planning problems generated from one scenario
        :return: list of dynamic obstacles
        :return: list of planning problem sets
        """
        lanelet_network = self.lanelet_network
        self.ego_id_list = []

        # find some ego vehicles
        self.logger.debug('start searching for interesting ego vehicles')
        num_planning_pro, ego_list, obs_list, obs_list_with_ego = self._choose_ego_from_obstacles(planning_pro_per_scen,
                                                                                                  obstacles)

        list_obstacles = []
        list_obstacles_with_ego = []  # used when parameter "visualize_ego" is true
        list_planning_problem_set = []
        for i in range(num_planning_pro):
            ego = ego_list[i]
            ###############################################
            # get ego vehicle ids
            ego_id = ego.obstacle_id
            self.ego_id_list.append(ego_id)
            ###############################################

            obstacles_short = obs_list[i]
            ####################################################################
            # Keep only the initial state of vehicles
            for id, obstacle in obstacles_short.items():
                obstacle.prediction.trajectory.state_list = [obstacle.initial_state]
            #####################################################################

            # define planning problem id
            planing_problem_id = 1

            # define initialState
            initial_pos = ego.initial_state.position
            initial_v = ego.initial_state.velocity
            initial_orientation = ego.initial_state.orientation
            initial_yaw_rate = 0.0
            initial_slip_angle = 0.0
            initial_time_step = ego.initial_state.time_step
            initial_state = State(position=initial_pos,
                                  velocity=initial_v,
                                  orientation=initial_orientation,
                                  yaw_rate=initial_yaw_rate,
                                  slip_angle=initial_slip_angle,
                                  time_step=initial_time_step)

            # define goalState using the final state
            last_state = ego.prediction.trajectory.final_state
            goal_center = last_state.position
            goal_orientation = last_state.orientation

            goal_state = last_state
            goal_state.position = Rectangle(length=6, width=2, center=goal_center, orientation=goal_orientation)
            goal_state.time_step = Interval(goal_state.time_step - 1, goal_state.time_step)

            goal_state = State(time_step=goal_state.time_step,
                               position=goal_state.position)
            state_list = [goal_state]
            goal_region = GoalRegion(state_list)

            # define goalState using the final lanelet
            if planning_pro_with_lanelet is True:
                lanelet_of_goal_position = lanelet_network.find_lanelet_by_position([goal_center])[0]  # list of id
                if len(lanelet_of_goal_position) > 0:
                    self.logger.debug(f'{i + 1}th goal lanelet defined at lanelet {lanelet_of_goal_position[0]}')
                    goal_lanelet = {0: lanelet_of_goal_position}
                    state_list[0].position = lanelet_network.find_lanelet_by_id(
                        lanelet_of_goal_position[0]).convert_to_polygon()
                    goal_region = GoalRegion(state_list, goal_lanelet)
                else:
                    self.logger.warning(f'No goal lanelet found for the {i + 1}th planning problem.')
                    break

            # combine elements of a planning problem and generate planning problem set
            planning_problem = PlanningProblem(planing_problem_id, initial_state, goal_region)
            planning_problem_set = PlanningProblemSet()
            planning_problem_set.add_planning_problem(planning_problem)

            list_obstacles.append(obstacles_short)
            list_planning_problem_set.append(planning_problem_set)
            if visualize_ego is True:
                obstacles_with_ego = obs_list_with_ego[i]
                ####################################################################
                list_with_ego_initail_state = []
                list_obstacles_with_ego.append(obstacles_with_ego)
                #####################################################################

                list_obstacles_with_ego.append(obstacles_with_ego)
                ###############################################################

        return list_obstacles, list_obstacles_with_ego, list_planning_problem_set

    def write_cr_file_and_video(self, i, scenario_counter, create_video=False, check_validity=True):
        """
        Write commonroad scenario file and create corresponding videos.
        :param i: the i-th map
        :param scenario_counter: counter for generated example_scenarios from the i-th map
        :return: nothing
        """
        output_dir_name = os.path.join(self.scenario_folder, '../')
        # create for each planning problem a maps scenario file and the corresponding videos
        generated_scenarios = 0
        for k in range(len(self.list_cr_scenarios)):
            commonroad_scenario = self.list_cr_scenarios[k]

            if check_validity:
                if check_collision(commonroad_scenario._dynamic_obstacles) is True:
                    warnings.warn('<write_cr_file_and_video> Collision detected! Skipping scenario.')
                    continue
                else:
                    self.logger.info('Scenario contains no collision.')

            planning_problem_set = self.list_planning_problem_set[k]

            scen_name = self.conf_scenario.map_name + "-" + str(i) + "_" + str(k + 1 + scenario_counter) + "_I"

            filename = os.path.join(output_dir_name, scen_name + '.xml')
            # write maps file without ego
            self.write_final_cr_file(filename, commonroad_scenario, planning_problem_set, check_validity)
            self.logger.info(f"Commonroad scenario file created for {k + 1 + scenario_counter}th planning problem")

            # write maps file with ego
            if self.conf_scenario.visualize_ego:
                commonroad_scenario_with_ego = self.list_cr_scenarios_with_ego[k]
                filename2 = os.path.join(output_dir_name, scen_name + '.with_ego.xml')
                self.write_final_cr_file(filename2, commonroad_scenario_with_ego)
                self.logger.info(f"Commonroad scenario file with ego created for"
                                 f"{k + 1 + scenario_counter} th planning problem")

            generated_scenarios += 1
            if create_video is True:
                # create ego centered video
                if self.conf_scenario.visualize_ego is True:
                    cr_scenario_with_ego = self.list_cr_scenarios_with_ego[k]
                    ego_vehicle = cr_scenario_with_ego.obstacle_by_id(self.conf_scenario.default_ego_id)
                    video_center_traj = []
                    ego_state_list = ego_vehicle.prediction.trajectory.state_list
                    for state in ego_state_list:
                        video_center_traj.append(state.position)
                    video_with_ego_path = os.path.join(output_dir_name, scen_name + '_with_ego.mp4')
                    self.logger.info(f'Create video at {video_with_ego_path}')
                    create_scenario_video(
                        [cr_scenario_with_ego, planning_problem_set],
                        time_begin=0,
                        delta_time_steps=3,
                        time_end=self.conf_scenario.cr_scenario_time_steps,
                        file_path=video_with_ego_path,
                        plot_limits=None,
                        draw_params={
                            'scenario': {'dynamic_obstacle': {'show_label': self.conf_scenario.visualize_veh_id},
                                         'lanelet_network': {
                                             'lanelet': {'show_label': self.conf_scenario.visualize_lanelet_id}}}},
                        fps=10,
                        dpi=120)
                self.logger.info(f"Video created for {k + 1 + scenario_counter}th planning problem (ego visualized)")

        return generated_scenarios
