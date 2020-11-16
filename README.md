# Commonroad Interactive Benchmarks
![CHN_Sha-16_2_I-1](example_scenarios/gif/CHN_Sha-16_2_I-1.gif)

Package for creating interactive scenarios in the CommonRoad framework. 

## Installation

This project uses conda. Make sure it is installed before proceeding with the installation.

1. Create a new environment
    You can use your environment with python version 3.7, or create a new one by running
    ```bash
    conda create -n cr37 python=3.7
    ```
   
2. Configure git
    If you don't want to enter your git credentials many times, cou can configure `git` to save it automatically:
    ```bash
    git config --global credential.helper store
    ```

3. Install the dependencies
    **To install the dependencies of the module**, simply run
    ```bash
    bash install.sh -e cr37 --sumo
    ```
    If you wish to use the SUMO-Manager, run
    ```bash
    bash install.sh -e cr37 --sumo_manager
    ```
   
   This will create an `install` folder, pull all the dependencies and install them there
   
    **Note:** `cr37` needs to be replaced by the name of your conda environment if needed.
   
4. Update the environment variables
    If you have installed SUMO, the corresponding SUMO_PATH has been written into the `~/.profile` file. To reach this variable from an IDE, you must **sign-out and sing-in** (in Linux)



### Installed dependencies
The following modules will be installed using the install script
*  The previous work [Commonroad_Scenarios](https://gitlab.lrz.de/ss19/commonroad_scenarios)
*  [SUMO-CommonRoad Interface](https://gitlab.lrz.de/cps/sumo-interface/-/tree/interactive_SS20)
*  [Anaconda](https://docs.anaconda.com/anaconda/install/)
*  [commonroad-sumo-manager](https://gitlab.lrz.de/cps/commonroad-sumo-manager), if needed.

## Usage

### Convert static CommonRoad scenario to interactive
To convert a static CommonRoad scenario interactive scenario use the script `scenario_converter/convert_scenarios.py`. 
```bash
python -m scenario_converter.convert_scenarios 
```
**Arguments:**
* `--cr_scneario`: Path to the CommonRoad scenario, which will be converted. 
**Default:** `./example_scenarios/cr_scenario/DEU_A9-2_1_T-1.xml`
* `--output`: Path to the output folder
**Default:** `/example_scenarios/output`
* `--video`: Flag, indicates whether video should be created or not
**Default:** `False`
* `--config`: Configuration type of the simulation
**Default:** `CONFIG_TYPE.SUMO_CONFIG_1`

This script will convert to interactive scenario as follows:
1. Read the CommonRoad scenario and uses it's lanelet network to create SUMO lane-network
2. Convert the route of all obstacles to SUMO route definition

### Generate interactive CommonRoad scenarios using SUMO
To generate interactive scenarios use the script `scenario_generator/generate_scenarios.py`. 
```bash
python -m scenario_generator.generate_scenarios 
```
**Arguments:**
* `--cr_maps`: Path to the folder which contains the CommonRoad scenarios, which maps will be used for the scenarios generation. 
**Note:** *Currently only the files in this folder will be gathered, no recursive search is implemented.* 
**Default:** `/example_scenarios/maps/test`
* `--output`: Path to the output folder
**Default:** `/example_scenarios/output`
* `--video`: Flag, indicates whether video should be created or not
**Default:** `False`
* `--num_max_resimulation`: Sets the maximum number of resimulation
**Default:** `10`

This script will generate interactive scenarios as follows:
1. Read the CommonRoad scenarios from the passed folder and keep their lanelet network
2. Generate artificial traffic using SUMO
3. Search for interesting vehicles to be marked as ego, e.g. lane changing, strong breaking, etc.
4. If no appropriate vehicle has been found, repeat from 2. (but maximum 10 times), otherwise create planning problem from the chosen vehicle

## Determinism checker
Checking whether a scenario is deterministic or not by two means:
*  Simulate the scenario multiple times, compare the simulated scenarios.
*  Read rou.xml file and check if any key parameters are set to 'random'. 

To check interactive scenarios use the script `scenario_generator/generate_scenarios.py`. 
```bash
python -m determinism_checker.check_determinism 
```
**Arguments:**
* `--scenario_folder_path`: Path to the folder which contains the files of the interactive CommonRoad scenario, which will be checked. 
**Note:** *This script checks the determinism of only one scenario* 
**Default:** `Scenarios/CHN_Cho-1-1/CHN_Cho-1_1_I`
* `--output_folder_path`: Path to the output folder
**Default:** `/example_scenarios/output`
* `--video`: Flag, indicates whether video should be created or not
**Default:** `False`
* `--num_of_simulations`: Sets the number of simulation
**Default:** `5`
* `--sumo_manager`: Flag, indicates whether using sumo-manager or not
**Default:** `False`

## Interactive scenario evaluation
To evaluate a solution for an interactive scenario, you can consider next to the resulted simulated scenario the intact scenario where the ego vehicle had no influence the traffic too. You can find the implementation in the script `evaluation/evaluate_solution.py`. 
**Note:** The concrete evaluation is not implemented yet, just a skeleton.

### Simulate a solution
To evaluate a solution, the interactive scenario must be simulated with the solution trajectory. For this reason you can use the script `evaluation/simulate_solution.py`. 
```bash
python -m evaluation.simulate_solution 
```
**Arguments:**
* `--input_scenario`: Path to the folder which contains the files of the interactive CommonRoad scenario. 
**Default:** `./example_scenarios/interactive/DEU_A9-2_1_I-1-1`
* `--solution`: Path to the output folder
**Default:** `./example_scenarios/solution/KS1:SA1:DEU_A9-2_1_T-1:2018b.xml`
* `--output`: Path to the output folder
**Default:** `./example_scenarios/gif`
* `--video`: Flag, indicates whether video should be created or not
**Default:** `False`
* `--sumo_manager`: Flag, indicates whether using sumo-manager or not
**Default:** `False`


## Testing
For further information, please check the [tests](tests) module.


## Known issues
### Scenario related issues
In case of a known scenario related issue `ScenarioException` is thrown. These cases should be further investigated with the author of the scenario and the responsible of the scenario testing. 
* Inconsistent lanelet-network - The successor-predecessor or adjacency relationships are not defined correctly
* Invalid obstacle - The obstacle has no trajectory defined

### Conversion related errors
The network simplification during the conversion results problems in many cases
* The simplified lanelet network contains internal edges which are merged from two original lanelet.  SUMO considers the internal lanes as separate lanes even if they have a common lanelet part. As a result, if there are one obstacle in the common part of the first internal lane and another obstacle in the common part of the 
* The simplified lanelet network contains no connection from a normal to an internal edge




## Examples
![DEU_A9-2_1_I-1](example_scenarios/gif/DEU_A9-2_1_I-1.gif)
![DEU_BadEssen-2_5_I-1](example_scenarios/gif/DEU_BadEssen-2_5_I-1.gif)
![DEU_Guetersloh-16_1_I-1](example_scenarios/gif/DEU_Guetersloh-16_1_I-1.gif)
![DEU_Guetersloh-20_4_I-1](example_scenarios/gif/DEU_Guetersloh-20_4_I-1.gif)
![DEU_Muehlhausen-5_1_I-1](example_scenarios/gif/DEU_Muehlhausen-5_1_I-1.gif)
![DEU_Muehlhausen-6_1_I-1](example_scenarios/gif/DEU_Muehlhausen-6_1_I-1.gif)
![DEU_Speyer-4_2_I-1](example_scenarios/gif/DEU_Speyer-4_2_I-1.gif)
![USA_US101-7_3_I-1](example_scenarios/gif/USA_US101-7_3_I-1.gif)
![USA_US101-26_2_I-1](example_scenarios/gif/USA_US101-26_2_I-1.gif)

## Issues during building SUMO-GUI
If you would like to build the SUMO-GUI, you can follow the procedure in the install script, however, you can encounter the following issues
* The GUI is not in the list of enabled features
* FOX is not found
* DSO missing from command line

In my case (Ubuntu 18.04) these problems can be resolved by copying the content of the folder `misc/sumo_gui` into the root of the `sumo`. This will fix some missing cmake modules and arguments. After overwriting the existing cmake files, you can rebuild the cmake files and build SUMO. 
