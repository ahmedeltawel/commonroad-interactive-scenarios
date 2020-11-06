""""
Script which evaluates a solution trajectory for an interactive scenario
"""
import argparse
import sys

import matplotlib as mpl

from evaluation.simulate_solution import simulate_interactive_solution

mpl.use('TkAgg')

# load parameters

__author__ = "Peter Kocsis"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.1"
__maintainer__ = "Moritz Klischat"
__email__ = "moritz.klischat@tum.de"
__status__ = "Integration"


def evaluate_solution_argsparser() -> argparse.ArgumentParser:
    """Returns a parser for the script's arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input_scenario", type=str,
        default="./example_scenarios/interactive/DEU_A9-2_1_I-1-1",
        help="Path to the interactive scenario"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="./example_scenarios/output", help="Output folder path",
    )
    parser.add_argument(
        "-s", "--solution", type=str,
        default="./example_scenarios/solution/KS1:SA1:DEU_A9-2_1_T-1:2018b.xml",
        help="Path to the CommonRoad solution file"
    )
    parser.add_argument(
        "-v", "--video", action="store_true", default=False, help="Create video",
    )
    return parser


def evaluate_interactive_solution(scenario_without_ego, scenario_with_ego) -> float:
    # TODO: Implement evaluation here
    return 0


def evaluate_interactive_solution_file(interactive_scenario_folder: str,
                                  solution_file: str,
                                  output_folder_path: str = None,
                                  creating_video: bool = False) -> float:
    simulated_scenario_without_ego, simulated_scenario_with_ego = simulate_interactive_solution(interactive_scenario_folder, solution_file, output_folder_path, creating_video)

    return evaluate_interactive_solution(simulated_scenario_without_ego, simulated_scenario_with_ego)



if __name__ == '__main__':
    arguments = evaluate_solution_argsparser().parse_args(sys.argv[1:])
    evaluate_interactive_solution_file(interactive_scenario_folder=arguments.input_scenario,
                                       output_folder_path=arguments.output,
                                       solution_file=arguments.solution,
                                       creating_video=arguments.video)
