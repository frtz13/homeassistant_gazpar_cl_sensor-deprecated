#!/bin/sh

SCRIPT=$(readlink -f "$0")
BASE_DIR=$(dirname "${SCRIPT}")
export BASE_DIR
CFG_FILE="gazpar.cfg"
export PYTHONWARNINGS="ignore"

run_script () {
  PY_SCRIPT="gazpar_ha.py"
  PY_SCRIPT="${BASE_DIR}"/"${PY_SCRIPT}"
  python3 "${PY_SCRIPT}" $1 -o "${BASE_DIR}" 2>&1
}

# check requirements and configuration file
if [ $# -eq 1 ]
then
  # only call for this command line parameter to avoid calling pip install too often
  if [ $1 = "delete" ]
  then
    pip install -r "$BASE_DIR"/requirements.txt 1>"$BASE_DIR"/pip.log 2>"$BASE_DIR"/piperror.log
  fi
fi

if [ -f "${BASE_DIR}"/"${CFG_FILE}" ]
then
  . "${BASE_DIR}"/"${CFG_FILE}"
  export GAZPAR_USERNAME
  export GAZPAR_PASSWORD
  run_script $1 
else
    echo "Config file is missing ["${BASE_DIR}"/"${CFG_FILE}"]"
    exit 1
fi