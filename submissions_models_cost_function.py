import sys
from abc import abstractmethod, ABC, abstractproperty
import math
import numpy as np
#from pycrcc import Circle
#from commonroad_cc.collision_detection.pycrcc_collision_dispatch import create_collision_checker
from scipy.integrate import simps
from scipy.spatial import distance


class PartialCostException(Exception):
    pass


class PartialCostFunction(ABC):

    @abstractproperty
    def id(self):
        pass

    @classmethod
    @abstractmethod
    def evaluate(cls, scenario, vehicle_model, trajectory) -> float:
        pass

    @classmethod
    def _sq_distance_to_line_segment(cls, p, p1, p2):
        # Calculate the squared distance of point p to the line segment between p1 and p2
        # Code slightly modified and translated to Python from:
        # https://stackoverflow.com/questions/849211/shortest-distance-between-a-point-and-a-line-segment

        a = p[0] - p1[0]
        b = p[1] - p1[1]
        c = p2[0] - p1[0]
        d = p2[1] - p1[0]

        dot = a * c + b * d
        len_sq = c ** 2 + d ** 2

        if len_sq != 0:
            param = dot / len_sq
        else:
            param = -1

        if param < 0:
            xx = p1[0]
            yy = p1[1]
        elif param > 1:
            xx = p2[0]
            yy = p2[1]
        else:
            xx = p1[0] + param * c
            yy = p1[1] + param * d

        dx = p[0] - xx
        dy = p[1] - yy

        return dx ** 2 + dy ** 2


class Acceleration(PartialCostFunction):
    id = 'A'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        velocity = [state.velocity for state in trajectory.state_list]
        acceleration = np.diff(velocity) / scenario.dt
        acceleration_sq = np.square(acceleration)
        cost = simps(acceleration_sq, dx=scenario.dt)
        return cost


class Jerk(PartialCostFunction):
    id = 'J'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        velocity = [state.velocity for state in trajectory.state_list]
        acceleration = np.diff(velocity) / scenario.dt
        jerk = np.diff(acceleration) / scenario.dt
        jerk_sq = np.square(jerk)
        cost = simps(jerk_sq, dx=scenario.dt)
        return cost


class SteeringAngle(PartialCostFunction):
    id = 'SA'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        steering_angle = [state.steering_angle for state in trajectory.state_list]
        steering_angle_sq = np.square(steering_angle)
        cost = simps(steering_angle_sq, dx=scenario.dt)
        return cost


class SteeringRate(PartialCostFunction):
    id = 'SR'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        steering_angle = [state.steering_angle for state in trajectory.state_list]
        steering_rate = np.diff(steering_angle) / scenario.dt
        steering_rate_sq = np.square(steering_rate)
        cost = simps(steering_rate_sq, dx=scenario.dt)
        return cost


class YawRate(PartialCostFunction):
    id = 'Y'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        orientation = [state.orientation for state in trajectory.state_list]
        yaw_rate = np.diff(orientation) / scenario.dt
        yaw_rate_sq = np.square(yaw_rate)
        cost = simps(yaw_rate_sq, dx=scenario.dt)
        return cost


class LaneCenterOffset(PartialCostFunction):
    id = 'LC'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        lanelet_network = scenario.lanelet_network

        dists_to_lane_centers = []
        for state in trajectory.state_list:
            position = state.position
            closest_lanelets = lanelet_network.find_lanelet_by_position([position])[0]

            if len(closest_lanelets) == 0:
                raise Exception("No closest lanelet found for state at timestep " + str(state.time_step))

            closest_lanelet = lanelet_network.find_lanelet_by_id(closest_lanelets[0])
            cv = closest_lanelet.center_vertices
            min_dist_sq = sys.float_info.max
            for i in range(len(cv) - 1):
                p1 = cv[i]
                p2 = cv[i + 1]
                p = position
                d_sq = cls._sq_distance_to_line_segment(p, p1, p2)
                min_dist_sq = min(min_dist_sq, d_sq)

            dists_to_lane_centers.append(math.sqrt(min_dist_sq))

        dists_to_lane_centers_sq = np.square(dists_to_lane_centers)
        cost = simps(dists_to_lane_centers_sq, dx=scenario.dt)
        return cost


class VelocityOffset(PartialCostFunction):
    id = 'V'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        lanelet_network = scenario.lanelet_network

        velocity_offsets = []
        for state in trajectory.state_list:
            position = state.position
            velocity = state.velocity
            closest_lanelets = lanelet_network.find_lanelet_by_position([position])[0]

            if len(closest_lanelets) == 0:
                raise Exception("No closest lanelet found for state at timestep " + str(state.time_step))

            closest_lanelet = lanelet_network.find_lanelet_by_id(closest_lanelets[0])
            speed_limit = closest_lanelet.speed_limit
            if speed_limit is None or math.isinf(speed_limit):
                velocity_offsets.append(0)
            else:
                velocity_offsets.append((speed_limit - velocity) ** 2)

        cost = simps(velocity_offsets, dx=scenario.dt)
        return cost


class OrientationOffset(PartialCostFunction):
    id = 'O'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        lanelet_network = scenario.lanelet_network

        orientation_offsets = []
        for state in trajectory.state_list:
            position = state.position
            orientation = state.orientation
            closest_lanelets = lanelet_network.find_lanelet_by_position([position])[0]

            if len(closest_lanelets) == 0:
                raise Exception("No closest lanelet found for state at timestep " + str(state.time_step))

            closest_lanelet = lanelet_network.find_lanelet_by_id(closest_lanelets[0])
            goal_orientation = cls._find_lane_segment_orientation(closest_lanelet, state)
            orientation_offsets.append((orientation - goal_orientation) ** 2)

        cost = simps(orientation_offsets, dx=scenario.dt)
        return cost

    @classmethod
    def _find_lane_segment_orientation(cls, lanelet, state):
        cv = lanelet.center_vertices
        min_dist_sq = sys.float_info.max
        orientation = 0
        p = state.position
        for i in range(0, len(cv) - 1):
            p1 = cv[i]
            p2 = cv[i + 1]
            d_sq = cls._sq_distance_to_line_segment(p, p1, p2)
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
                orientation = math.atan((p2[1] - p1[1]) / (p2[0] - p1[0]))
        return orientation


class DistanceToObstacles(PartialCostFunction):
    id = 'D'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        length = vehicle_model.length
        width = vehicle_model.width
        xis = []
        for state in trajectory.state_list:
            collision_checker = create_collision_checker(scenario)
            xis.append(np.math.exp(-cls._measure_distance_to_obstacles(state, width, length, collision_checker)))

        cost = simps(xis, dx=scenario.dt)
        return cost

    @classmethod
    def _measure_distance_to_obstacles(cls, state, width, length, collision_checker):
        # TODO this function is bugged
        r = math.sqrt(2 * ((width / 2) ** 2))
        x = state.position[0]
        y = state.position[1]
        orientation = state.orientation
        x_start = x - 0.5 * (length - width) * np.cos(orientation)
        y_start = y - 0.5 * (length - width) * np.sin(orientation)
        circle_count = int(math.ceil(length / width))
        d = (length - width) / (circle_count - 1)
        circle_centers = []
        for i in range(0, circle_count):
            x_circle = x_start + i * d * np.cos(orientation)
            y_circle = y_start + i * d * np.sin(orientation)
            circle_centers.append((x_circle, y_circle))
        ds = []
        for cc in circle_centers:
            if collision_checker.collide(Circle(r, cc[0], cc[1])):
                ds.append(r)
            else:
                ds.append(cls._find_collision_free_circle(collision_checker, cc, min_radius=r))
        d_min = min(ds)
        return d_min - r

    @classmethod
    def _find_collision_free_circle(cls, collision_checker, pt, min_radius=1.8, max_radius=1000.0, precision=0.125):
        """
        The returned radius is collision free, the radius + stepsize_abort collides if it is < max_radius.
        """
        inner_circle_radius = min_radius
        outer_circle_radius = inner_circle_radius

        # if collision_checker.collide(Circle(min_radius, pt[0], pt[1])):
        #     raise Exception()

        '''Searches for a colliding circle by increasing circle radius by 2 every time.'''
        while not collision_checker.collide(Circle(outer_circle_radius, pt[0], pt[1])):
            inner_circle_radius = outer_circle_radius
            if outer_circle_radius >= max_radius:
                break
            outer_circle_radius = min(max_radius, 2 * outer_circle_radius)

        '''Searches for the approximate collision free circle depending on the precision value'''
        while np.abs(inner_circle_radius - outer_circle_radius) > precision:
            test_radius = 0.5 * (inner_circle_radius + outer_circle_radius)
            if collision_checker.collide(Circle(test_radius, pt[0], pt[1])):
                outer_circle_radius = test_radius
            else:
                inner_circle_radius = test_radius

        return inner_circle_radius


class PathLength(PartialCostFunction):
    id = 'L'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        velocity = [state.velocity for state in trajectory.state_list]
        cost = simps(velocity, dx=scenario.dt)
        return cost


class Time(PartialCostFunction):
    id = 'T'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        cost = len(trajectory.state_list) * scenario.dt
        return cost


class CostFunctionException(Exception):
    pass


class CostFunction:
    COST_FUNCTION_DICT = {
        "JB1": [(Time, 1.0)],

        "SA1": [(SteeringAngle, 0.1),
                (SteeringRate, 0.1),
                (DistanceToObstacles, 100000.0)],

        "WX1": [(Time, 10.0),
                (VelocityOffset, 1.0),
                (Acceleration, 0.1),
                (Jerk, 0.1),
                (DistanceToObstacles, 0.1),
                (LaneCenterOffset, 10.0)],

        "SM1": [(Acceleration, 50.0),
                (SteeringAngle, 50.0),
                (SteeringRate, 50.0),
                (LaneCenterOffset, 1.0),
                (VelocityOffset, 20.0),
                (OrientationOffset, 50.0)],

        "SM2": [(Acceleration, 50.0),
                (SteeringAngle, 50.0),
                (SteeringRate, 50.0),
                (LaneCenterOffset, 1.0),
                (OrientationOffset, 50.0)],

        "SM3": [(Acceleration, 50.0),
                (SteeringAngle, 50.0),
                (SteeringRate, 50.0),
                (VelocityOffset, 20.0),
                (OrientationOffset, 50.0)],

        # "MW1": [("J_lat", 5), ("J_lon", 0.5), ("V_lon", 0.2), ("ID", 1)], TODO J_lon J_lat V_lon ??
    }

    def __init__(self, cost_id):
        if cost_id not in self.COST_FUNCTION_DICT:
            raise CostFunctionException("Cost function is not defined! Partial Cost ID:", cost_id)

        self.id = cost_id
        self.partial_costs = self.COST_FUNCTION_DICT[cost_id]

    @property
    def partial_cost_ids(self):
        return [partial_cost.id for partial_cost, weight in self.partial_costs]

    @property
    def partial_cost_weights(self):
        return [weight for partial_cost, weight in self.partial_costs]

    def is_vehicle_supported(self, vehicle):
        if not hasattr(vehicle, 'supported_partial_costs'):
            return True

        for pc in self.partial_costs:
            if pc[0].id not in vehicle.supported_partial_costs:
                return False

        return True

    def evaluate(self, scenario, vehicle_model, trajectory) -> (float, dict):
        partial_cost_results = {pcost.id: (pcost.evaluate(scenario, vehicle_model, trajectory), weight)
                                for pcost, weight in self.partial_costs}
        total_cost = sum([cost * weight for cost_id, (cost, weight) in partial_cost_results.items()])
        return {'cost': total_cost, 'partial_cost_results': partial_cost_results}



class ClosestDistance(PartialCostFunction):
    id = 'CD'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        a = 9001        #current minimal distance
        i = 0           #current time step
        t = 0           #time step the near collision happend
        for state in trajectory.state_list:
            position = state.position
            for dyn_obs in scenario.dynamic_obstacles:
                b = dyn_obs.prediction.trajectory.state_at_time_step(i)
                if b is not None :
                    if distance.euclidean(position, b.position) < a :
                        a = distance.euclidean(position, b.position)
                        t =i
            i = i + 1
        #print(t)
        return a

class ClosestDistanceExtended(PartialCostFunction):  #under development
    #the idea is the delete random spawning and other nonderministic behavior as an other condition is added.
    #The distance had to get smaller from time step i-1 to time step i
    #to ignore e.g. vehicles spawning next to each other.
    #as scenarios should get 100% deterministic in the futute this function is not needed
    id = 'CD'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        a = 9001
        t = 0
        id = None
        i = 0
        for state in trajectory.state_list:
            position = state.position
            for dyn_obs in scenario.dynamic_obstacles:
                b = dyn_obs.prediction.trajectory.state_at_time_step(i)
                d = dyn_obs.prediction.trajectory.state_at_time_step(i-1)
                if b is not None and d is not None:
                    k = distance.euclidean(position, b.position)
                    if k < a : #distance has to be smaller than the old maximum
                        c = distance.euclidean(trajectory.state_list[i-1].position, d.position )
                        if k<c: #distance has to be larger in the last time step
                            a = distance.euclidean(position, b.position)
                            t = i
                            id = dyn_obs.obstacle_id
            i = i + 1
        print("Ego vehicle is close to "+str(id)+" at time step "+str(t)+" with "+str(a))
        return a




class AvgSpeed(PartialCostFunction):
    id = 'AS'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        sum_of_data = 0
        counted_data = 0
        i = 0
        for dyn_obs in scenario.dynamic_obstacles:
            state = dyn_obs.prediction.trajectory.state_at_time_step(i)
            if state is not None:
                sum_of_data = sum_of_data + state.velocity
                counted_data = counted_data + 1
            i = i+1
        return sum_of_data/counted_data


class StrongesBreake(PartialCostFunction):
    id = 'SB'

    @classmethod
    def evaluate(cls, scenario, vehicle_model, trajectory):
        current_strongest_break = 0
        distance = 50
        current_timestep = 0
        for dyn_obs in scenario.dynamic_obstacles:
            state = dyn_obs.prediction.trajectory.state_at_time_step(current_timestep)
            if state is not None:
                if current_strongest_break > state.acceleration and distance.euclidean(trajectory.state_at_time_step(current_timestep).position, state.position)<distance:
                    current_strongest_break = state.acceleration
                    #print('new strong brake found')
            current_timestep = current_timestep+1
        return current_strongest_break




#no sufficient testing done!
class Evaluation:    #meant for testing with more ego vehicles and more scenarios.

    @classmethod
    def Distance(cls,scenario, trajectory_list):
        a=0
        for trajectory in trajectory_list:
            b= ClosestDistance.evaluate(scenario, None, trajectory)
            if b>a:
                a=b
        return a

    @classmethod
    def Breake(cls,scenario, trajectory_list):
        a = 0
        for trajectory in trajectory_list:
            b = StrongesBreake.evaluate(scenario, None, trajectory)
            if b < a:
                a = b
        return a

    @classmethod
    def Speed(cls,scenario, scenario_without_ego):
        return AvgSpeed.evaluate(scenario_without_ego, None, None) - AvgSpeed.evaluate(scenario, None, None)

    @classmethod
    def Position(cls,scenario, scenario_without_ego, trajectory_list):

        a = 0
        b = 0
        t = 0

        while t < len(trajectory_list[0].state_list):
            for i in range (len(scenario.dynamic_obstacles)):
                with_ego = scenario.dynamic_obstacles[i].prediction.trajectory.state_at_time_step(t)
                without_ego = scenario_without_ego.dynamic_obstacles[i].prediction.trajectory.state_at_time_step(t)
                if with_ego is not None and without_ego is not None:
                    a = a + distance.euclidean(without_ego.position, with_ego.position)
                    b = b +1
            t = t+1

        return a/b

    #with no testing possibility it does not make sense to extend this approach















