#!/bin/sh

SCRIPT=$(readlink -f "$0")
BASE_DIR=$(dirname "${SCRIPT}")
export BASE_DIR
CFG_FILE="gaspar.cfg"
LOG_FILE="gaspar.log"
export PYTHONWARNINGS="ignore"

run_script () {
  PY_SCRIPT="gaspar_ha.py"
  PY_SCRIPT="${BASE_DIR}"/"${PY_SCRIPT}"
  python3 "${PY_SCRIPT}" $1 -o "${BASE_DIR}" 2>&1
}

# check configuration file
if [ -f "${BASE_DIR}"/"${CFG_FILE}" ]
then
  . "${BASE_DIR}"/"${CFG_FILE}"
  export GASPAR_USERNAME
  export GASPAR_PASSWORD
  run_script $1 
else
    echo "Config file is missing ["${BASE_DIR}"/"${CFG_FILE}"]"
    exit 1
fi