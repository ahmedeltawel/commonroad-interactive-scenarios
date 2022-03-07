import glob
import os
import pickle
from copy import deepcopy

from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.scenario import ScenarioID
from configHighway import SumoConfigHighway
from simulation.simulations import load_sumo_configuration
from sumocr.sumo_config import DefaultConfig

migration_dict_replace = {
    "veh_params" : {
        "motorcycle": ObstacleType.MOTORCYCLE,
        "passenger": ObstacleType.CAR,
        "truck": ObstacleType.TRUCK,
        "bus": ObstacleType.BUS,
        "bicycle": ObstacleType.BICYCLE,
        "pedestrian":ObstacleType.PEDESTRIAN,
    }
}

def replace_veh_params(conf):
    veh_params = getattr(conf, "veh_params")
    for old, new in migration_dict_replace["veh_params"].items():
        for veh_attr, attr_dict in veh_params.items():
            if new not in attr_dict:
                attr_dict[new] = attr_dict[old]

            if old in attr_dict:
                del attr_dict[old]

    setattr(conf, "veh_params", veh_params)


def add_country_code(conf: DefaultConfig):
    conf.country_id = ScenarioID.from_benchmark_id(conf.scenario_name, "2020a").country_id


def migrate_config_file(path: str):
    assert path.endswith(".p")
    with open(path, "rb") as input_file:
        conf = pickle.load(input_file)

    conf.lateral_resolution = 0.5
    conf.scenarios_path = None
    replace_veh_params(conf)
    # add_country_code(conf)
    # if hasattr(conf, "scenarios_path"):
    #     delattr(conf.__class__, "scenarios_path")

    print(path)
    return conf


def migrate_competition(path):
    conf = deepcopy(DefaultConfig())
    assert path.endswith(".p")
    with open(path, "rb") as input_file:
        conf_load = pickle.load(input_file)

    # print(conf_load.__dict__)
    for attr in dir(conf):
        if attr.startswith('__') or callable(getattr(conf, attr)):
            continue
        setattr(conf, attr, getattr(conf_load, attr))

    conf.scenarios_path = None
    del conf._abc_impl
    # print(conf.__dict__)
    return conf

if __name__ == "__main__":
    interactive_scenario_path = "/home/klischat/Downloads/competition_scenarios/interactive"
    interactive_scenario_path_out = "/home/klischat/Downloads/competition_scenarios_new/interactive"
    for config_file in glob.glob(os.path.join(interactive_scenario_path, "**/*.p"), recursive=True):
        # conf = migrate_config_file(str(config_file))
        config_file_out = os.path.join(interactive_scenario_path_out,
                                       os.path.basename(os.path.dirname(config_file)),
                                       os.path.basename(config_file))
        if not os.path.isfile(config_file_out):
            continue
        conf = migrate_competition(str(config_file))
        # print(config_file)
        # print(conf.scenario_name)
        with open(config_file_out, 'wb') as f:
            pickle.dump(conf, f)

    # from sumocr.sumo_config import DefaultConfig
    for config_file in glob.glob(os.path.join(interactive_scenario_path_out, "**/*.p"), recursive=True):
        # conf = migrate_config_file(str(config_file))
        print(config_file)
        with open(config_file, "rb") as input_file:
            conf_load = pickle.load(input_file)
        print(conf_load.scenario_name)