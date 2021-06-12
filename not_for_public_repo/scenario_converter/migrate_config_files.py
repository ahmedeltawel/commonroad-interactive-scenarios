import glob
import os
import pickle

from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.scenario import ScenarioID
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


if __name__ == "__main__":
    interactive_scenario_path = "/home/klischat/GIT_REPOS/commonroad-scenarios-dev/scenarios"
    for config_file in glob.glob(os.path.join(interactive_scenario_path, "**/*.p"), recursive=True):
        conf = migrate_config_file(str(config_file))
        print(config_file)
        with open(config_file, 'wb') as f:
            pickle.dump(conf, f)
