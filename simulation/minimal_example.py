""""
Minimal example to simulate interactive scenarios
"""
__author__ = "Edmond Irani Liu"
__copyright__ = "TUM Cyber-Physical System Group"
__credits__ = []
__version__ = "0.3"
__maintainer__ = "Edmond Irani Liu"
__email__ = "edmond.irani@tum.de"
__status__ = "Integration"

import matplotlib as mpl
from commonroad.common.solution import CommonRoadSolutionReader

mpl.use('TkAgg')

from commonroad.scenario.scenario import Tag
from simulation import simulate_without_ego, simulate_with_solution, simulate_with_planner


def main():
    # specify required arguments
    name_scenario = "USA_US101-26_2_I-1-1"
    path_scenario = "../scenarios/interactive/NGSIM/US101/" + name_scenario

    # for simulation with a given solution trajectory
    name_solution = "KS2:SM1:USA_US101-26_2_T-1:2020a"
    path_solution = "../scenarios/solutions/" + name_solution + ".xml"
    solution = CommonRoadSolutionReader.open(path_solution)

    # path to store output GIFs
    path_output = "../scenarios/gifs"

    # scenario_without_ego, pps = simulate_without_ego(interactive_scenario_path=path_scenario,
    #                                                  output_folder_path=path_output,
    #                                                  create_GIF=True,
    #                                                  use_sumo_manager=False)

    scenario_with_solution, pps = simulate_with_solution(interactive_scenario_path=path_scenario,
                                                         output_folder_path=path_output,
                                                         solution=solution,
                                                         create_GIF=True,
                                                         use_sumo_manager=False)

    # scenario_with_solution, pps = simulate_with_planner(interactive_scenario_path=path_scenario,
    #                                                     output_folder_path=path_output,
    #                                                     create_GIF=True,
    #                                                     use_sumo_manager=False)
    #
    # # simulate interactive scenario with and without ego vehicle
    # scenario_without_ego, scenario_with_ego, pps = simulate_with_solution(interactive_scenario_path=path_scenario,
    #                                                                       solution_file=path_solution,
    #                                                                       output_folder_path=path_output,
    #                                                                       create_GIF=True,
    #                                                                       use_sumo_manager=False)

    author = 'Max Mustermann'
    affiliation = 'Technical University of Munich, Germany'
    source = ''
    tags = {Tag.URBAN}
    path_scenarios_simulated = "../scenarios/simulated/"

    # # write simulated scenarios to file
    # # without ego
    # fw = CommonRoadFileWriter(scenario_without_ego, pps, author, affiliation, source, tags)
    # fw.write_to_file(f"{path_scenarios_simulated}{name_scenario}_no_ego.xml", OverwriteExistingFile.ALWAYS)

    # # with solution
    # if scenario_with_solution:
    #     fw = CommonRoadFileWriter(scenario_with_solution, pps, author, affiliation, source, tags)
    #     fw.write_to_file(f"{path_scenarios_simulated}{name_scenario}_solution.xml", OverwriteExistingFile.ALWAYS)


if __name__ == '__main__':
    main()
