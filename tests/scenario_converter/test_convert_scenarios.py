"""
Module tests of the module scenario_generator
"""
import os
import re
from pathlib import Path

from configuration import CONFIG_TYPE
from crmapconverter.sumo_map.cr2sumo import ScenarioException
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

resource_path = os.path.join(resource_root("commonroad-scenarios"), "scenarios")
output_path = output_root("test_convert_scenarios")

exception_whitelist = (ScenarioException,)


def collect_trajectory_based_scenarios(root_path: str):
    all_scenarios = [str(path.relative_to(root_path)) for path in Path(root_path).rglob('*.xml')]
    pattern = re.compile(r".+\d+_\d+_T-\d+\.xml")
    return [scenario for scenario in all_scenarios if pattern.match(scenario)]


@pytest.mark.timeout(300)
@pytest.mark.parametrize(
    ("scenario_rel_path"),
    # ['hand-crafted/DEU_Muc-2_1_T-1.xml'],
    collect_trajectory_based_scenarios(resource_path),
)
@module_test
@functional
def test_convert_scenarios(scenario_rel_path):
    scenario_path = os.path.join(resource_path, scenario_rel_path)

    try:
        successful_conversion = convert_scenario(cr_scenario_path=scenario_path,
                                                 output_folder_path=output_path,
                                                 config_type=CONFIG_TYPE.SUMO_CONFIG_1,
                                                 use_sumo_manager=False,
                                                 creating_video=False)
    except Exception as exp:
        if not isinstance(exp, exception_whitelist):
            raise exp
        else:
            pytest.skip(str(exp))
            return

    assert successful_conversion
