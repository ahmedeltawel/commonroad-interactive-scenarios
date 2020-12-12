__author__ = "Anna-Katharina Rettinger"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["CoPlan"]
__version__ = "0.1"
__maintainer__ = "Anna-Katharina Rettinger"
__email__ = "commonroad-i06@in.tum.de"
__status__ = "Beta"

import enum
from typing import List, Dict, Tuple, Type

import numpy as np
import ipywidgets as widgets
import matplotlib.pyplot as plt
from IPython import display
from IPython.display import display
from commonroad.geometry.shape import Rectangle
from commonroad.planning.planning_problem import PlanningProblem, PlanningProblemSet
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.scenario.obstacle import ObstacleType, DynamicObstacle
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.trajectory import State, Trajectory
# import CommonRoad-io modules
from commonroad.visualization.draw_dispatch_cr import draw_object
from ipywidgets import widgets
from matplotlib.lines import Line2D

# import Motion Automaton modules


list_states_nodes = None


def visualize_solution(scenario: Scenario, planning_problem_set: PlanningProblemSet, trajectory: Trajectory) -> None:
    from IPython import display
    num_time_steps = max(len(trajectory.state_list),len(scenario.obstacles[0].prediction.trajectory.state_list))
#     num_time_steps = len(scenario.obstacles[0].prediction.trajectory.state_list)
    # create the ego vehicle prediction using the trajectory and the shape of the obstacle
    dynamic_obstacle_initial_state = trajectory.state_list[0]
    dynamic_obstacle_shape = Rectangle(width=1.8, length=4.3)
    dynamic_obstacle_prediction = TrajectoryPrediction(trajectory, dynamic_obstacle_shape)

    # generate the dynamic obstacle according to the specification
    dynamic_obstacle_id = scenario.generate_object_id()
    dynamic_obstacle_type = ObstacleType.CAR
    dynamic_obstacle = DynamicObstacle(dynamic_obstacle_id,
                                       dynamic_obstacle_type,
                                       dynamic_obstacle_shape,
                                       dynamic_obstacle_initial_state,
                                       dynamic_obstacle_prediction)

    # visualize scenario
    for i in range(0, num_time_steps):
        display.clear_output(wait=True)
        plt.figure(figsize=(25, 10))
        draw_object(scenario, draw_params={'time_begin': i})
        draw_object(planning_problem_set)
        draw_object(dynamic_obstacle,
                    draw_params={'time_begin': i,
                                 'dynamic_obstacle': {'shape': {'facecolor': 'green'},
                                                      'trajectory': {'draw_trajectory': True,
                                                                     'facecolor': '#ff00ff',
                                                                     'draw_continuous': True,
                                                                     'z_order': 60,
                                                                     'line_width': 5}
                                                      }
                                 })

        plt.gca().set_aspect('equal')
        plt.show()



