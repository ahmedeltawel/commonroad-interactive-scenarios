"""
Check the determinism of example_scenarios by comparing difference of state values
"""
import argparse
import os
import sys
from pathlib import Path

from determinism_checker.route_file_checker import rou_file_determinism_check
from determinism_checker.simulation_checker import resimulate_scenario, plot_vehicle_trajectories, \
    obstacle_determinism_check

__author__ = "Peter Kocsis, Yueming Li"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"


def check_determinism_argsparser() -> argparse.ArgumentParser:
    """Returns a parser for the script's arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--scenario_folder_path", type=str, default=os.path.join(os.getcwd(),
                                                                       "example_scenarios",
                                                                       "interactive",
                                                                       "DEU_A9-2_1_I-1-1"),
        help="Path to the folder contains the scenario which should be checked"
    )
    parser.add_argument(
        "-ns", "--num_of_simulations", type=int, default=5, help="Number of simulations used during determinism check"
    )
    parser.add_argument(
        "-o", "--output_folder_path", type=str, default=os.path.join(os.getcwd(), "determinism_check"),
        help="Path to the output folder for the videos"
    )
    parser.add_argument(
        "-v", "--video", action="store_true", default=False, help="Create video",
    )
    parser.add_argument(
        "-sm", "--sumo_manager", action="store_true", default=False, help="Using the sumo-manager",
    )
    return parser


def check_determinism(scenario_file_path: str,
                      num_of_simulations: int,
                      output_folder_path: str = None,
                      use_sumo_manager: bool = False,
                      creating_video: bool = False,
                      std_tolerance: float = 0.1) -> bool:
    """
    Checks a single interactive scenario for determinism
    Steps: 1. Check the rou files for determinism
           2. Check the behaviour of the obstacles by simulating the traffic many times
              and creating statistics from the trajectory of a single obstacle
    :param scenario_file_path: Path to the interactive scenario
    :param num_of_simulations: The number of simulations whioch will be performed for statistics gathering
    :param output_folder_path: Path to the output folder for the videos
    :param use_sumo_manager: Indicates whether to use the sumo-manager
    :param creating_video: Indicates whether to create video
    :param std_tolerance: Tolerance of the standard deviation of the obstacles' trajectory state values
    :return: True if all the deviations are in the given tolerance
    """
    assert not creating_video or output_folder_path is not None, \
        "The output folder path was not defined for video creation"

    simulated_scenarios = resimulate_scenario(scenario_file_path, num_of_simulations,
                                              use_sumo_manager, creating_video, output_folder_path)

    # Plot trajectories
    if creating_video:
        plot_vehicle_trajectories(simulated_scenarios)

    # Check rou files for determinism
    print("Checking the route files")
    sumo_files, _ = os.path.splitext(scenario_file_path)
    filenames = list(Path(sumo_files).rglob("*.rou.xml"))
    if filenames:
        is_rou_files_deterministic = [rou_file_determinism_check(str(rou_file)) for rou_file in filenames]
        if all(is_rou_files_deterministic):
            is_rou_files_deterministic = True
            print("The rou files are deterministic")
        else:
            is_rou_files_deterministic = False
            print("The rou files are not deterministic")
    else:
        is_rou_files_deterministic = False
        print(f"No rou file has been found in {scenario_file_path}")

    # Check vehicles for determinism
    print("Checking the obstacles' trajectories")
    is_vehicle_deterministic = obstacle_determinism_check(simulated_scenarios, std_tolerance)

    is_deterministic = is_vehicle_deterministic and is_rou_files_deterministic
    if is_deterministic:
        print("The scenario is deterministic.")

    return is_deterministic


if __name__ == '__main__':
    arguments = check_determinism_argsparser().parse_args(sys.argv[1:])
    check_determinism(scenario_file_path=arguments.scenario_folder_path,
                      num_of_simulations=arguments.num_of_simulations,
                      output_folder_path=arguments.output_folder_path,
                      use_sumo_manager=arguments.sumo_manager,
                      creating_video=arguments.video)
