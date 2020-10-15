"""
Module tests of the module scenario_generator
"""
import os
from pathlib import Path

import pytest
import time
import numpy as np

from configuration import CONFIG_TYPE
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

@pytest.mark.parametrize(
    ("scenario_rel_path"),
    [str(path.relative_to(resource_path)) for path in Path(resource_path).rglob('*.xml')],
)
@module_test
@functional
def test_convert_scenarios(scenario_rel_path):
    scenario_path = os.path.join(resource_path, scenario_rel_path)

    successful_conversion = convert_scenario(cr_scenario_path=scenario_path,
                                             output_folder_path=output_path,
                                             config_type=CONFIG_TYPE.SUMO_CONFIG_1,
                                             use_sumo_manager=False,
                                             creating_video=False)

    assert successful_conversion
