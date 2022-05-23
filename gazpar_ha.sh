#!/bin/sh

# v. 2021.10.22

SCRIPT=$(readlink -f "$0")
BASE_DIR=$(dirname "${SCRIPT}")
export BASE_DIR
export PYTHONWARNINGS="ignore"

run_script () {
  PY_SCRIPT="gazpar_ha.py"
  PY_SCRIPT="${BASE_DIR}"/"${PY_SCRIPT}"
  python3 "${PY_SCRIPT}" $1 $2 $3 $4 -o "${BASE_DIR}" 2>&1
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

run_script $1 $2 $3 $4
