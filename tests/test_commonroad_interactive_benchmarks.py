"""
Module tests of the module scenario_generator
"""
import os
import re
from pathlib import Path

from configuration import CONFIG_TYPE
from crmapconverter.sumo_map.cr2sumo import ScenarioException
from determinism_checker.check_determinism import check_determinism
from evaluation.simulate_solution import simulate_interactive_solution
from scenario_converter.convert_scenarios import convert_scenario
from tests.common.marker import *
from tests.common.path import resource_root, output_root


__author__ = "Peter Kocsis"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Peter Kocsis"
__email__ = "peter.kocsis@tum.de"
__status__ = "Integration"

resource_path = {"2018b": os.path.join(resource_root("commonroad-scenarios"), "scenarios"),
                 "2020a": os.path.join(resource_root("commonroad-scenarios_2020"), "scenarios")}
output_path = output_root("test_commonroad_interactive_benchmarks.py")

exception_whitelist = (ScenarioException, )


def collect_trajectory_based_scenarios(root_path: str, commonroad_version: str):
    all_scenarios = [str(path.relative_to(root_path)) for path in Path(root_path).rglob('*.xml')]
    pattern = re.compile(r".+\d+_\d+_T-\d+\.xml")
    return [(commonroad_version, scenario) for scenario in all_scenarios if pattern.match(scenario)]


# @pytest.mark.timeout(300)
@pytest.mark.parametrize(
    ("commonroad_version", "scenario_rel_path"),
    # [("2018b", 'NGSIM/US101/USA_US101-3_1_T-1.xml'),
    # ("2018b", 'NGSIM/US101/USA_US101-15_3_T-1.xml'),
    # ("2018b", 'NGSIM/US101/USA_US101-13_1_T-1.xml')],
    collect_trajectory_based_scenarios(resource_path["2018b"], "2018b"),# +
    # collect_trajectory_based_scenarios(resource_path["2020a"], "2020a"),
)
@integration_test
@functional
def test_interactive_scenario_simulation(commonroad_version, scenario_rel_path):
    scenario_path = os.path.join(resource_path[commonroad_version], scenario_rel_path)
    scenario_output_folder = os.path.join(output_path, commonroad_version, os.path.dirname(scenario_rel_path))

    try:
        successful_conversion, interactive_scenario_folder = \
            convert_scenario(cr_scenario_path=scenario_path,
                             output_folder_path=scenario_output_folder,
                             config_type=CONFIG_TYPE.SUMO_CONFIG_1,
                             creating_video=False)
        assert successful_conversion

        deterministic_simulation = check_determinism(scenario_file_path=interactive_scenario_folder,
                                                     num_of_simulations=2)
        assert deterministic_simulation

    except Exception as exp:
        if not isinstance(exp, exception_whitelist):
            raise exp
        else:
            pytest.skip(str(exp))
            return


