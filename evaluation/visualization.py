""""
Script which evaluates a solution trajectory for an interactive scenario
"""
import os
import warnings
from typing import Union, List, Dict

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from commonroad.geometry.shape import Rectangle
from commonroad.planning.planning_problem import PlanningProblem
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.scenario.obstacle import ObstacleType, DynamicObstacle
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.trajectory import Trajectory
from commonroad.visualization.draw_dispatch_cr import draw_object
from matplotlib.animation import FuncAnimation

__author__ = "Peter Kocsis, Daniel Tar, Edmond Irani"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"


def create_gif(scenario: Scenario, output_path: str,
               planning_problem: PlanningProblem = None,
               trajectory: Trajectory = None,
               secondary_scenario: Scenario = None,
               follow_ego: bool = False) -> None:

    frame_count_padding = int(
        1 / scenario.dt
    )  # add short padding to create a short break before the loop (1sec)

    if trajectory is not None:
        frame_count = len(trajectory.state_list) + frame_count_padding
        # create the ego vehicle prediction using the trajectory and the shape of the obstacle
        dynamic_obstacle_initial_state = trajectory.state_list[0]

        dynamic_obstacle_shape = Rectangle(width=1.8, length=4.3)
        dynamic_obstacle_prediction = TrajectoryPrediction(trajectory, dynamic_obstacle_shape)

        # generate the dynamic obstacle according to the specification
        dynamic_obstacle_id = scenario.generate_object_id()
        dynamic_obstacle_type = ObstacleType.CAR
        ego_dynamic_obstacle = DynamicObstacle(dynamic_obstacle_id,
                                               dynamic_obstacle_type,
                                               dynamic_obstacle_shape,
                                               dynamic_obstacle_initial_state,
                                               dynamic_obstacle_prediction)
    else:
        frame_count = max(
            [obstacle.prediction.final_time_step for obstacle in scenario.obstacles]) + frame_count_padding
        ego_dynamic_obstacle = None

    if follow_ego:
        if trajectory is not None:
            # a dictionary that holds the plot limits at each time step
            dict_plot_limits = get_dynamic_plot_limits(trajectory, frame_count)
        else:
            warnings.warn("Unable to follow the ego vehicle is no trajectory is provided!")
            dict_plot_limits = get_plot_limits(scenario, frame_count)
    else:
        dict_plot_limits = get_plot_limits(scenario, frame_count)

    fig_num = os.getpid()

    interval = (
            1000 * scenario.dt
    )  # delay between frames in milliseconds, 1 second * dt to get actual time in ms

    dpi = 150
    if secondary_scenario is not None:
        figsize = (10,5)
    else:
        figsize = (5,5)
    fig = plt.figure(fig_num, dpi=dpi, figsize=figsize)

    if secondary_scenario is not None:
        ax_main = fig.add_subplot(121)
        ax_secondary = fig.add_subplot(122)
        ax_main.axis('equal')
        ax_secondary.axis('equal')

        ax_main.set_title('Main')
        ax_secondary.set_title('Secondary')
    else:
        ax_main = fig.gca()
        ax_main.axis('equal')

    (ln,) = plt.plot([], [], animated=True)

    main_scenario_handle = {}
    secondary_scenario_handle = {}
    ego_dyn_obstacle_handle = {}

    def init_plot():
        fig.suptitle(str(scenario.scenario_id))
        if secondary_scenario is not None:
            draw_object(secondary_scenario, plot_limits=dict_plot_limits[0], ax=ax_secondary,
                        handles=secondary_scenario_handle)
            if planning_problem is not None:
                draw_object(planning_problem, plot_limits=dict_plot_limits[0], ax=ax_secondary,
                            handles=secondary_scenario_handle)

        draw_object(scenario, plot_limits=dict_plot_limits[0], ax=ax_main, handles=main_scenario_handle)
        if planning_problem is not None:
            draw_object(planning_problem, plot_limits=dict_plot_limits[0], ax=ax_main, handles=main_scenario_handle)
        if ego_dynamic_obstacle is not None:
            draw_object(ego_dynamic_obstacle, plot_limits=dict_plot_limits[0], ax=ax_main, handles=ego_dyn_obstacle_handle,
                        draw_params={'time_begin': 0,
                                     'dynamic_obstacle': {'shape': {'facecolor': 'green'}}})
        fig.tight_layout()
        return (ln,)

    def animate_plot(frame):
        if secondary_scenario is not None:
            redraw_dynamic_obstacles(secondary_scenario.dynamic_obstacles,
                                     handles=secondary_scenario_handle,
                                     plot_limits=dict_plot_limits[frame],
                                     ax=ax_secondary,
                                     figure_handle=fig,
                                     draw_params={'time_begin': frame}, draw=False)

        redraw_dynamic_obstacles(scenario.dynamic_obstacles,
                                 handles=main_scenario_handle,
                                 plot_limits=dict_plot_limits[frame],
                                 ax=ax_main,
                                 figure_handle=fig,
                                 draw_params={'time_begin': frame}, draw=False)
        if ego_dynamic_obstacle is not None:
            redraw_dynamic_obstacles([ego_dynamic_obstacle],
                                     handles=ego_dyn_obstacle_handle,
                                     plot_limits=dict_plot_limits[frame],
                                     ax=ax_main,
                                     figure_handle=fig,
                                     draw_params={'time_begin': frame,
                                                  'dynamic_obstacle': {'shape': {'facecolor': 'green'}}}, draw=False)

        return (ln,)

    anim = FuncAnimation(fig, animate_plot, frames=frame_count, init_func=init_plot, blit=True, interval=interval)

    file_name = str(scenario.scenario_id) + os.extsep + 'gif'
    print(f"Saving {file_name}")
    anim.save(os.path.join(output_path, file_name), dpi=dpi, writer="ffmpeg")
    plt.close(fig)
    print(f"{file_name} saved")

def get_plot_limits(scenario: Scenario, frame_count):
    """
    The plot limits track the center of the ego vehicle.
    """
    def flatten(list_to_flat):
        return [item for sublist in list_to_flat for item in sublist]
    center_vertices = np.array(flatten([lanelet.center_vertices for lanelet in scenario.lanelet_network.lanelets]))

    min_coords = np.min(center_vertices, axis=0)
    max_coords = np.max(center_vertices, axis=0)
    dict_plot_limits = [[min_coords[0],
                         max_coords[0],
                         min_coords[1],
                         max_coords[1]]] * frame_count

    return dict_plot_limits


def get_dynamic_plot_limits(trajectory: Trajectory, frame_count, area_size=30):
    """
    The plot limits track the center of the ego vehicle.
    """
    num_time_step_trajectory = len(trajectory.state_list)

    dict_plot_limits = list()
    for i in range(frame_count):
        if i < num_time_step_trajectory:
            state = trajectory.state_list[i]
        else:
            state = trajectory.state_list[num_time_step_trajectory - 1]

        dict_plot_limits.append([state.position[0] - area_size,
                                 state.position[0] + area_size,
                                 state.position[1] - area_size,
                                 state.position[1] + area_size])

    return dict_plot_limits


def redraw_dynamic_obstacles(dyn_obst_list: List[DynamicObstacle],
                             handles: Dict[int, List[mpl.patches.Patch]],
                             figure_handle: mpl.figure.Figure,
                             ax: Union[None, mpl.axes.Axes] = None,
                             draw_params=None, plot_limits: Union[List[Union[int, float]], None] = None,
                             draw: bool = True) -> None:
    """
    This function is used for fast updating dynamic obstacles of an already drawn plot. Saves on average about 80% time
    compared to a complete plot.
    Deletes all dynamic obstacles which are specified in handles and draws dynamic obstacles of a scenario.

    :param dyn_obst_list: dynamic obstacles
    :param handles: dict of obstacle_ids and corresponding patch handles (generated by draw_object function)
    :param draw_params:
    :param plot_limits: axis limits for plot [x_min, x_max, y_min, y_max]
    :param figure_handle: figure handle of current plot
    :param draw: if True, updates are displayed directly in figure
    :return: None
    """
    if ax is None:
        ax = figure_handle.gca()
    # remove dynamic obstacle from current plot
    for handles_i in handles.values():
        for handle in handles_i:
            if handle is not None:
                handle.remove()
    handles.clear()

    # redraw dynamic obstacles
    draw_object(dyn_obst_list, draw_params=draw_params, plot_limits=plot_limits, ax=ax, handles=handles)

    # update plot
    if draw is True:
        for handles_i in handles.values():
            for handle in handles_i:
                if handle is not None:
                    ax.draw_artist(handle)

        if mpl.get_backend() == 'TkAgg':
            figure_handle.canvas.draw()

        elif mpl.get_backend() == 'Qt5Agg':
            figure_handle.canvas.update()
        else:
            try:
                figure_handle.canvas.update()
            except:
                raise Exception(
                    '<plot_helper/redraw_dynamic_obstacles> Backend for matplotlib needs to be \'Qt5Agg\' or \'TkAgg\' but is'
                    '\'%s\'' % mpl.get_backend())

        figure_handle.canvas.flush_events()
