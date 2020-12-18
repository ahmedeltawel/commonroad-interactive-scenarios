# CommonRoad Interactive Scenarios
This package provides the functionality of simulating interactive CommonRoad scenarios. Given the trajectory
of the ego vehicle specified by the planning problem, the behavior of other traffic participants are simulated
with [SUMO](https://sumo.dlr.de/docs/index.html).

The code is written in Python 3.7 and has been tested on Ubuntu 18.04.

## Installation
This project uses Conda. It should be installed before proceeding with the installation.

1. Creating a new environment
    You can either use your existing environment which has Python version 3.7, or create a new one by running
    
    ```bash
    conda create -n cr37 python=3.7
   ```
   
   Here the environment is named `cr37`.
   
2. Configuring Git

    If you don't want to enter your Git credentials many times, you can configure it to save them automatically:
    ```bash
    git config --global credential.helper store
    ```

3. Installing the dependencies

   The following commands install the dependencies of this package, which include:

   - [CommonRoad-SUMO Interface](https://gitlab.lrz.de/tum-cps/commonroad-sumo-interface)
   - [CommonRoad SUMO Manager](https://gitlab.lrz.de/cps/commonroad-sumo-manager) (optional)

   If you wish to install SUMO locally, run

   ```bash
   bash install.sh -e cr37 --sumo
   ```
   If you wish to use the SUMO Manager (which dockerizes SUMO in a container), run
   ```bash
   bash install.sh -e cr37 --sumo_manager
   ```

   This will create an `install` folder, pull all the dependencies and install them there.

    **Note:** If your Conda environment has a name different from `cr37`, it should be replaced in the above commands.

4. Updating the environment variables

    If you have installed SUMO locally, the `SUMO_PATH` environment variable has been written into the `~/.profile` file. To reach this variable from an IDE (e.g., PyCharm), you must **reboot your system**.

## Usage

XXXX to be added.

## Examples

Below, we compare a selection of scenarios. The `Main` and `Secondary` plots show the scenario with and without the ego vehicle, respectively.

![CHN_Sha-16_2_I-1](example_scenarios/gif/CHN_Sha-16_2_I-1.gif)
![DEU_Guetersloh-20_4_I-1](example_scenarios/gif/DEU_Guetersloh-20_4_I-1.gif)
![USA_US101-7_3_I-1](example_scenarios/gif/USA_US101-7_3_I-1.gif)
![USA_US101-26_2_I-1](example_scenarios/gif/USA_US101-26_2_I-1.gif)

## Issues during building SUMO GUI
If you would like to build the SUMO-GUI, you can follow the procedure in the install script; however, you might encounter the following issues
* The GUI is not in the list of enabled features
* FOX is not found
* DSO missing from command line

Under Ubuntu 18.04, these problems can be resolved by copying the content of the folder `misc/sumo_gui` into the root folder of `sumo`. This will fix the modules missing issues. After overwriting the existing CMake files, you should rebuild the CMake files and build the SUMO again. 
