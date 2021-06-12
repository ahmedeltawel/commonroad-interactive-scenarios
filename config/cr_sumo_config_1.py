"""
Default configuration for CommonRoad to SUMO map converter
"""
from typing import Dict, Union

from commonroad.common.util import Interval
from commonroad.scenario.obstacle import ObstacleType
from sumocr.sumo_config.default import DefaultConfig

from .cr_sumo_config_base import CRSumoConfigBase


class CRSumoConfig_1(CRSumoConfigBase):

    def __init__(self):
        # logging level for logging module
        super().__init__()
        self.__class__ = DefaultConfig
        self.config_id = 1

        self.logging_level = 'INFO'  # select DEBUG, INFO, WARNING, ERROR, CRITICAL

        self.scenario_name: str = ''

        # simulation
        self.dt = 0.1  # length of simulation step of the interface
        self.delta_steps = 1  # number of sub-steps simulated in SUMO during every dt
        self.presimulation_steps = 2  # number of time steps before simulation with ego vehicle starts
        self.simulation_steps = 200  # number of simulated (and synchronized) time steps
        self.with_sumo_gui = False
        # lateral resolution > 0 enables SUMO'S sublane model, see https://sumo.dlr.de/docs/Simulation/SublaneModel.html
        self.lateral_resolution = 1.0
        # re-compute orientation when fetching vehicles from SUMO.
        # Avoids lateral "sliding" at lane changes at computational costs
        self.compute_orientation = True

        # [m/s] if not None: use this speed limit instead of speed limit from CommonRoad files
        self.overwrite_speed_limit = 130 / 3.6
        # [m/s] default max. speed for SUMO for unrestricted sped limits
        self.unrestricted_max_speed_default = 120 / 3.6
        # [m] shifted waiting position at junction (equivalent to SUMO's contPos parameter)
        self.wait_pos_internal_junctions = -4.0
        # [m/s] default speed limit when no speed_limit is given
        self.unrestricted_speed_limit_default = 130 / 3.6

        # ego vehicle
        self.ego_start_time: int = 0

        # ego vehicle sync parameters
        #
        # Time window to detect the lanelet change in seconds
        self.lanelet_check_time_window = int(2 / self.dt)
        # The absolute margin allowed between the planner position and ego position in SUMO
        self.protection_margin = 2.0
        # Variable can be used  to force the consistency to certain number of steps
        self.consistency_window = 4
        # Used to limit the sync mechanism only to move xy
        self.lane_change_sync = False
        # tolerance for detecting start of lane change
        self.lane_change_tol = 0.00
        self.ego_veh_width = 1.6
        self.ego_veh_length = 4.3

        # TRAFFIC GENERATION
        #
        # max. number of vehicles per km
        self.max_veh_per_km: int = 70
        # random seed for deterministic sumo traffic generation
        self.random_seed: int = 1234

        # probability distribution of different vehicle classes. Do not need to sum up to 1.
        veh_distribution = {
            ObstacleType.CAR: 4,
            ObstacleType.TRUCK: 0.8,
            ObstacleType.BUS: 0.3,
            ObstacleType.BICYCLE: 0.2,
            ObstacleType.PEDESTRIAN: 0
        }

        # default vehicle attributes to determine edge restrictions

        # vehicle attributes
        veh_params = {
            # maximum length
            'length': {
                ObstacleType.CAR: 5.0,
                ObstacleType.TRUCK: 7.5,
                ObstacleType.BUS: 12.4,
                ObstacleType.BICYCLE: 2.,
                ObstacleType.PEDESTRIAN: 0.415
            },
            # maximum width
            'width': {
                ObstacleType.CAR: 2.0,
                ObstacleType.TRUCK: 2.6,
                ObstacleType.BUS: 2.7,
                ObstacleType.BICYCLE: 0.68,
                ObstacleType.PEDESTRIAN: 0.678
            },
            'minGap': {
                ObstacleType.CAR: 2.5,
                ObstacleType.TRUCK: 2.5,
                ObstacleType.BUS: 2.5,
                # default 0.5
                ObstacleType.BICYCLE: 1.,
                ObstacleType.PEDESTRIAN: 0.25
            },
            'accel': {
                # default 2.9 m/s²
                ObstacleType.CAR: Interval(1.8, 2.9),
                # default 1.3
                ObstacleType.TRUCK: Interval(1, 1.5),
                # default 1.2
                ObstacleType.BUS: Interval(1, 1.4),
                # default 1.2
                ObstacleType.BICYCLE: Interval(1, 1.4),
                # default 1.5
                ObstacleType.PEDESTRIAN: Interval(1.3, 1.7),
            },
            'decel': {
                # default 7.5 m/s²
                ObstacleType.CAR: Interval(4, 6.5),
                # default 4
                ObstacleType.TRUCK: Interval(3, 4.5),
                # default 4
                ObstacleType.BUS: Interval(3, 4.5),
                # default 3
                ObstacleType.BICYCLE: Interval(2.5, 3.5),
                # default 2
                ObstacleType.PEDESTRIAN: Interval(1.5, 2.5),
            },
            'maxSpeed': {
                # default 180/3.6 m/s
                ObstacleType.CAR: 180 / 3.6,
                # default 130/3.6
                ObstacleType.TRUCK: 130 / 3.6,
                # default 85/3.6
                ObstacleType.BUS: 85 / 3.6,
                # default 85/3.6
                ObstacleType.BICYCLE: 25 / 3.6,
                # default 5.4/3.6
                ObstacleType.PEDESTRIAN: 5.4 / 3.6,
            }
        }

        # vehicle behavior
        """
        'minGap': minimum gap between vehicles
        'accel': maximum acceleration allowed
        'decel': maximum deceleration allowed (absolute value)
        'maxSpeed': maximum speed. sumo_default 55.55 m/s (200 km/h)
        'lcStrategic': eagerness for performing strategic lane changing. Higher values result in earlier lane-changing. sumo_default: 1.0
        'lcSpeedGain': eagerness for performing lane changing to gain speed. Higher values result in more lane-changing. sumo_default: 1.0
        'lcCooperative': willingness for performing cooperative lane changing. Lower values result in reduced cooperation. sumo_default: 1.0
        'sigma': [0-1] driver imperfection (0 denotes perfect driving. sumo_default: 0.5
        'speedDev': [0-1] deviation of the speedFactor. sumo_default 0.1
        'lcMaxSpeedLatStanding': max. lateral speed when vehicle is standing (avoids lateral sliding in standstill)
        """
        driving_params = {
            'lcStrategic': Interval(10, 100),
            'lcSpeedGain': Interval(3, 20),
            'lcCooperative': Interval(1, 3),
            'sigma': Interval(0.5, 0.65),
            'speedDev': Interval(0.1, 0.2),
            'speedFactor': Interval(0.9, 1.1),
            'lcImpatience': Interval(0, 0.5),
            'impatience': Interval(0, 0.5),
            'lcMaxSpeedLatStanding': 0,
            'lcSigma': Interval(0.1, 0.2),
            'lcKeepRight': Interval(0.8, 0.9)
        }