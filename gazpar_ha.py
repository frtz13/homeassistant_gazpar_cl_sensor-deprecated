#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Adapted to gaspar (C) 2018 epierre
# Adapted to Home Assistant by frtz13
# homeassistant_gazpar_cl_sensor

"""Returns energy consumption data from GRDF consumption data collected via their website (API).
"""

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import datetime
import logging
import sys
import base64
import json
import gazpar

PROG_VERSION = "2021.11.28"

BASEDIR = os.environ['BASE_DIR']

DAILY = "releve_du_jour"
DAILY_json = os.path.join(BASEDIR, DAILY + ".json")
DAILY_json_log = os.path.join(BASEDIR, "activity.log")

# command line commands
CMD_Fetch = "fetch"
CMD_Sensor = "sensor"
CMD_Sensor_Nolog = "sensor_nolog"
CMD_Delete = "delete"

KEY_INDEX_M3 = "index_m3"
KEY_INDEX_kWh = "index_kWh"
KEY_DATE = "date"
KEY_CONSO_kWh = "conso_kWh"
KEY_CONSO_m3 = "conso_m3"
KEY_NEWDATA = "new_data"

# Export the JSON file for daily consumption
def export_daily_values(res):
    with open(DAILY_json, 'w') as outfile:
        json.dump(res, outfile)

def add_daily_log():
    logging.basicConfig(filename=DAILY_json_log, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
#   set up logging to extra file
    #logToFile = logging.FileHandler(DAILY_json_log)
    #logToFile.level = logging.INFO
    #formatter = logging.Formatter('%(asctime)s %(message)s',"%Y-%m-%d %H:%M:%S")
    #logToFile.setFormatter(formatter)
    #logging.getLogger('').addHandler(logToFile)

def read_releve_from_file():
    try:
        if os.path.exists(DAILY_json):
            with open(DAILY_json, 'r') as infile:
                return json.load(infile)
        else:
            return None
    except Exception as e:
        logging.error("Error reading releve json file: " + str(e))
        return None


def fetch_data():
    """
    get data from GRDF
    write daily and monthly result to json files
    """
    add_daily_log()

    if len(sys.argv) < 7:
        logging.error(f"Pas assez de paramètres sur la ligne de commande ({len(sys.argv) - 1} au lieu de 6)")
        return False

    # we transfer login info in base64 encoded form to avoid any interpretation of special characters
    try:
        user_bytes = base64.b64decode(sys.argv[2])
        USERNAME = user_bytes.decode("utf-8")
        pwd_bytes = base64.b64decode(sys.argv[3])
        PASSWORD = pwd_bytes.decode("utf-8")
        PCE = sys.argv[4]
    except Exception as exc:
        logging.error(f"Cannot b64decode username ({sys.argv[2]}) or password ({sys.argv[3]}): " + str(exc))
        return False

# get saved consumption result and date, so we know when we will get new values
    daily_values = read_releve_from_file()
    if daily_values is None:
        old_date = "1970-01-01"
        old_index_kWh = 0
    else:
        old_date = daily_values[KEY_DATE]
        if KEY_INDEX_kWh in daily_values:
            old_index_kWh = daily_values[KEY_INDEX_kWh]
        else:
            old_index_kWh = 0
    try:
        grdf_client = gazpar.Gazpar(USERNAME, PASSWORD, PCE)
        result_json = grdf_client.get_consumption()
    except gazpar.GazparLoginException as exc:
        strErrMsg = "[Login error] " + str(exc)
        logging.error(strErrMsg)
        print("Error occurred: " + strErrMsg)
        return False
    except Exception as exc:
        strErrMsg = "[Error] " + str(exc)
        logging.error(strErrMsg)
        print(strErrMsg)
        return False
        
    try:
        dictLatest = result_json["releves"][-1]
        daily_values = {KEY_DATE: dictLatest["journeeGaziere"],
                        KEY_CONSO_kWh: dictLatest["energieConsomme"],
                        KEY_CONSO_m3: dictLatest["indexFin"] - dictLatest["indexDebut"],
                        KEY_INDEX_kWh: old_index_kWh + dictLatest["energieConsomme"],
                        KEY_INDEX_M3: dictLatest["indexFin"],
                        KEY_NEWDATA: True,
                        }
    except Exception as exc:
        strErrMsg = "[No data received] " + str(exc)
        logging.error(strErrMsg)
        print(str(strErrMsg))
        return False

    try:
        if (daily_values[KEY_DATE] is None) or (daily_values[KEY_DATE] == old_date):
            logging.info("No new data")
        else:
            logging.info("Received data")
            export_daily_values(daily_values)
        print("done.")
        return True
    except Exception as exc:
        strErrMsg = "[Data Export] " + str(exc)
        logging.error(strErrMsg)
        print(strErrMsg)
        return False
 

def sensor():
    """
    get conso from json result file
    get corresponding log
    send both back to Home Assistant
    """
    dailylog = ""
    add_daily_log()
    try:
        daily_values = read_releve_from_file()
        if daily_values is None:
            return False

        try:
            if os.path.exists(DAILY_json_log):
                with open(DAILY_json_log,"r") as logfile:
                    dailylog = logfile.read().splitlines()
        except:
            pass

        daily_values["log"] = "\r\n".join(dailylog)
        print(json.dumps(daily_values))
        return True
    except Exception as e:
        logging.error("Error reading result json file: " + str(e))
        return False


def delete_json():
    """
    prepare json releve file for next day
    reset daily conso to 'unknown'
    create index_kWh in json so the Sensor will have a 0 initial value
    """
    ok = True
    daily_values = read_releve_from_file()
    if daily_values is None:
        daily_values = {KEY_DATE: "1970-1-1",
                        KEY_CONSO_kWh: -1,
                        KEY_CONSO_m3: -1,
                        KEY_INDEX_kWh: 0,
                        KEY_NEWDATA: False,
                        }
    else:
        daily_values[KEY_CONSO_kWh] = -1
        daily_values[KEY_CONSO_m3] = -1
        daily_values[KEY_NEWDATA] = False
        if KEY_INDEX_kWh not in daily_values:
            daily_values[KEY_INDEX_kWh] = 0
    try:
        export_daily_values(daily_values)
    except Exception as e:
        #logging.ERROR("error when replacing json result file: " + str(e))
        print("error when replacing releve file: " + str(e))
        ok = False
    
    PREVIOUS_LOG = os.path.join(BASEDIR, "previous.log")
    try:
        if os.path.exists(PREVIOUS_LOG):
            os.remove(PREVIOUS_LOG)
        if os.path.exists(DAILY_json_log):
            os.rename(DAILY_json_log, PREVIOUS_LOG)
    except Exception as e:
        #logging.ERROR("error when deleting result log file: " + str(e))
        print("error when deleting/renaming log file: " + str(e))
        ok = False

    add_daily_log()
    logging.info(f"Script version {PROG_VERSION}")
    logging.info("reset daily conso")
    print("done.")
    return ok

# Main script 
def main():
    # we log to file and to a string which we include in the json result
#    logging.basicConfig(filename=BASEDIR + "/" + LOGFILE, format='%(asctime)s %(message)s', level=logging.INFO)
    
    arg_errmsg = f"use one of the following command line argugmnts: {CMD_Fetch}, {CMD_Sensor}, {CMD_Sensor_Nolog} or {CMD_Delete}"
    if len(sys.argv) > 3:
        if sys.argv[1] == CMD_Fetch:
            if not fetch_data():
                sys.exit(1)
        elif (sys.argv[1] == CMD_Sensor) or (sys.argv[1] == CMD_Sensor_Nolog):
            if not sensor():
                sys.exit(1)
        elif sys.argv[1] == CMD_Delete:
            if not delete_json():
                sys.exit(1)
        else:
            print(arg_errmsg)
    else:
        print(arg_errmsg)

if __name__ == "__main__":
    main()
