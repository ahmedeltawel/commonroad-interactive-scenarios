"""
Module tests of the module scenario_generator
"""
import os

import pytest
import time
import numpy as np
from scenario_generator.generate_scenarios import generate_scenarios
from tests.common.marker import *
from tests.common.path import resource_root, output_root

__author__ = "Peter Kocsis"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Peter Kocsis"
__email__ = "peter.kocsis@tum.de"
__status__ = "Integration"

resource_path = resource_root("test_generate_scenarios")
output_path = output_root("test_generate_scenarios")

@pytest.mark.parametrize(
    ("cr_maps", "expected_num_obtained_scenarios"),
    [("single_Ibbenbueren", 1),
     ("batch_SUMO", 3)],
)
@module_test
@functional
def test_generate_scenarios(cr_maps, expected_num_obtained_scenarios):
    """TODO: Unstable, because the seed of SUMO can't be set - if the seed can be set, this test become stable"""
    cr_maps_folder_path = os.path.join(resource_path, cr_maps)
    output_folder_path = os.path.join(output_path, cr_maps)

    num_obtained_scenarios = generate_scenarios(cr_maps_folder_path=cr_maps_folder_path,
                                                output_folder_path=output_folder_path)

    assert num_obtained_scenarios == expected_num_obtained_scenarios
