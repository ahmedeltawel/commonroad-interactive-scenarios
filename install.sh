#!/usr/bin/env bash

# Based on the implementation in the CommonRoad-RL and Commonroad-drivability-checker repository

# Constants
INSTALL_SUMO_MANAGER="FALSE"

USAGE="
$(basename "$0") [options] -- installs the dependencies for the commonroad-interactive-benchmark repo.
Options:
    -h | --help   show this help text
    -e ANACONDA_ENV | --env ANACONDA_ENV   name of the environment
    --sumo_manager   install the sumo-manager, default: false
"
# Parse args
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
  -h | --help)
    echo -e "${USAGE}"
    exit 1
    ;;

  -e | --env)
    ENVIRONMENT="$2"
    shift # past argument
    shift # past value
    ;;

  --sumo_manager)
    INSTALL_SUMO_MANAGER="TRUE"
    shift # past argument
    shift # past value
    ;;

  *) # unknown option
    shift              # past argument
    ;;
  esac
done


PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
JOBS=$(($(nproc) - 1))

source activate "$ENVIRONMENT"
which python

function safe_cd() {
  cd "${@}" || exit 255
}

function require_sudo() {
  if [[ $EUID -ne 0 ]]; then
    print_info "Permission required, using root."
    sudo ${@}
  else
    ${@}
  fi
}

function extract() {
  FILE="${1}"
  TYPE="${2}"
  if [ "$TYPE" = "zip" ]; then
    unzip -q -o "$FILE"
  elif [ "$TYPE" = "tar.gz" ]; then
    tar -xf --overwrite "$FILE"
  else
    echo "Unsupported archive format"
  fi
}

function get_ifnexist() {
  LINK=$2
  FILE="${LINK##*/}"
  TYPE="$1"
  wget -nv -nc "$LINK"
  extract "$FILE" "$TYPE"
}

mkdir -p install
safe_cd install

BASEDIR="$(pwd)"
function back_to_basedir() {
  safe_cd "${BASEDIR}"
}

echo "Installing build dependencies"
require_sudo apt-get install -y git unzip cmake


echo "Installing ffmpeg"
require_sudo apt-get install -y ffmpeg


echo "Installing CommonRoad_Scenarios SS19"
git clone https://gitlab.lrz.de/ss19/commonroad_scenarios.git
safe_cd commonroad_scenarios
git checkout 46c86a33b7cdda5f7c8a4847d7780db56bfe2b7d
git submodule update --init --recursive
pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"
conda install cartopy rtree numba
pip install -r requirements.txt

echo "Installing CommonRoad scenarios-features"
safe_cd commonroad-scenario-features
pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"
safe_cd ..

echo "Installing sumo-interface"
safe_cd sumo-interface
pip install -r requirements.txt
pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"

cp pathConfig_DEFAULT.py pathConfig.py
search="SUMO_BINARY = '/home/user/sumo/bin/sumo'"
replace="SUMO_BINARY = '${BASEDIR}/sumo/bin/sumo'"
sed -i "s+${search}+${replace}+g" pathConfig.py
if [ $? -eq 0 ]; then
    echo "SUMO_BINARY has been set"
else
    fail "Could not set SUMO_BINARY in pathConfig.py"
fi
back_to_basedir


echo "Installing CommonRoad map-tool"
git clone https://gitlab.lrz.de/cps/commonroad-map-tool.git
safe_cd commonroad-map-tool
git checkout 7025be62632b5a2c9759acee08c7ffc117173566
python setup.py install
back_to_basedir


echo "Installing SUMO"
require_sudo apt-get install python3 wget curl g++ libxerces-c-dev libfox-1.6-0 libfox-1.6-dev cmake libsqlite3-dev libgdal-dev libproj-dev libgl2ps-dev
git clone --recursive https://github.com/mo-kli/sumo.git
safe_cd sumo
git checkout 53edc58fcda9d534f9e95a7b66e127a766ed19d8
mkdir -p build/cmake-build
safe_cd build/cmake-build
cmake ../..
make -j $JOBS
safe_cd ../..
export SUMO_HOME="$PWD"
export PATH=$PATH:$SUMO_HOME/bin
echo "export SUMO_HOME=$SUMO_HOME" >> ~/.profile
echo "export PATH=$PATH:$SUMO_HOME/bin" >> ~/.profile
safe_cd tools
pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"
safe_cd ..
back_to_basedir


echo "Installing CommonRoad collision-checker"
git clone https://gitlab.lrz.de/tum-cps/commonroad-collision-checker.git
safe_cd commonroad-collision-checker
git checkout 197589618abc1dab44dffb89aed39b71b78786f4
mkdir -p build
safe_cd build
cmake -DADD_PYTHON_BINDINGS=TRUE -DPATH_TO_PYTHON_ENVIRONMENT="${CONDA_PREFIX}" -DPYTHON_VERSION="${PYTHON_VERSION}" -DCMAKE_BUILD_TYPE=Release ..
make -j $JOBS
safe_cd ..
python setup.py install
back_to_basedir


echo "Installing CommonRoad curvilinear-coordinate-system"
require_sudo apt-get install -y libomp-dev libcgal-dev libgmp-dev libglu1-mesa-dev
get_ifnexist zip https://syncandshare.lrz.de/dl/fiQ9ipcvfy9LFtnmrn1bHQQ7/commonroad-curvilinear-coordinate-system-fork-3211eb346d54b7e3641a3eec634cdc4040ae7213.zip
safe_cd commonroad-curvilinear-coordinate-system-fork-3211eb346d54b7e3641a3eec634cdc4040ae7213
pip install pyclipper
mkdir -p build
safe_cd build
cmake -DPYTHON_INCLUDE_DIR="${CONDA_PREFIX}/include/python${PYTHON_VERSION}m" -DPYTHON_LIBRARY="${CONDA_PREFIX}/lib/libpython${PYTHON_VERSION}m.so" -DPYTHON_EXECUTABLE="${CONDA_PREFIX}/bin/python${PYTHON_VERSION}m" -DCRCC_LIBRARY_DIR="$(pwd)/../../commonroad-collision-checker" -DADD_TESTS=False -DUSE_OMP=True -DCMAKE_BUILD_TYPE=Release ..
make -j "$JOBS"
safe_cd ..
pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"
back_to_basedir


if [ "${INSTALL_SUMO_MANAGER}" == "TRUE" ]; then
  echo "Installing CommonRoad-sumo-manager"
  git clone https://gitlab.lrz.de/cps/commonroad-sumo-manager.git
  pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"
  safe_cd commonroad-sumo-manager
  git checkout 47eb544ea85163ba3155a422603137d903de0796
  pip install -r ./requirements.txt
  back_to_basedir
fi

echo "Done"