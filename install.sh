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

source activate "$ENVIRONMENT"
which python

PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
JOBS=$(($(nproc) - 1))

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

echo "Installing dependencies"
pip install iso3166

echo "Installing build dependencies"
require_sudo apt-get install -y git unzip cmake


echo "Installing ffmpeg"
require_sudo apt-get install -y ffmpeg


echo "Installing CommonRoad-IO"
git clone https://gitlab.lrz.de/cps/commonroad-io.git
safe_cd commonroad-io
git checkout 573343c850bcdf138564c7b90f581a081875bda7
pip install -r requirements.txt
pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"
back_to_basedir


echo "Installing CommonRoad-Drivability-Checker"
git clone https://gitlab.lrz.de/tum-cps/commonroad-drivability-checker
safe_cd commonroad-drivability-checker
git checkout 28686ef451daa91f801f8e6e74959ac21deeced2
bash build.sh -e ${CONDA_PREFIX} -v 3.7 --cgal --serializer -i -j $JOBS
pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"
# WORKAROUND The place of the pycrcc library has been changed with the new crcc version, but thic change is not followed by pycrccosy
cp ./commonroad_dc/pycrcc.cpython-${PYTHON_VERSION//./}m-x86_64-linux-gnu.so ./pycrcc.cpython-${PYTHON_VERSION//./}m-x86_64-linux-gnu.so
cp ./commonroad_dc/libcrcc.a ./libcrcc.a
back_to_basedir


echo "Installing CommonRoad_Scenarios SS19"
git clone https://gitlab.lrz.de/ss19/commonroad_scenarios.git
safe_cd commonroad_scenarios
git checkout 636caeb08169c9c13d2d87e0619019934037ab07
git submodule update --init --recursive
conda install cartopy rtree numba
pip install -r requirements.txt
pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"

echo "Installing CommonRoad scenarios-features"
safe_cd commonroad-scenario-features
pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"
back_to_basedir


echo "Installing CommonRoad map-tool"
git clone https://gitlab.lrz.de/cps/commonroad-map-tool.git
safe_cd commonroad-map-tool
git checkout ab5cab2cc8782de54ee17ebdaef5e8d9a5f35634
pwd >> "${CONDA_PREFIX}/lib/python${PYTHON_VERSION}/site-packages/commonroad.pth"
back_to_basedir


echo "Installing sumo-interface"
git clone https://gitlab.lrz.de/cps/sumo-interface.git
safe_cd sumo-interface
git checkout ccca18f38b1d771dfb4895de8cba35d57b80b3c0
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


echo "Installing CommonRoad curvilinear-coordinate-system"
require_sudo apt-get install -y libomp-dev libcgal-dev libgmp-dev libglu1-mesa-dev
git clone https://gitlab.lrz.de/cps/commonroad-curvilinear-coordinate-system.git
safe_cd commonroad-curvilinear-coordinate-system
git checkout 2bc4923db22e3706a55df1f51740bec6dc0f159a
pip install pyclipper
mkdir -p build
safe_cd build
cmake -DPYTHON_INCLUDE_DIR="${CONDA_PREFIX}/include/python${PYTHON_VERSION}m" -DPYTHON_LIBRARY="${CONDA_PREFIX}/lib/libpython${PYTHON_VERSION}m.so" -DPYTHON_EXECUTABLE="${CONDA_PREFIX}/bin/python${PYTHON_VERSION}m" -DADD_TESTS=False -DADD_PYTHON_BINDINGS=True -DCMAKE_BUILD_TYPE=Release ..
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