#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Adapted to gaspar (C) 2018 epierre
# Adapted to Home Assistant by frtz13
# homeassistant_gazpar_cl_sensor

"""Returns energy consumption data from GrDf consumption data collected via their website (API).
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
from dateutil.relativedelta import relativedelta

PROG_VERSION = "2021.11.02"

BASEDIR = os.environ['BASE_DIR']

DAILY = "conso_par_jour"
DAILY_json = os.path.join(BASEDIR, DAILY + ".json")
DAILY_json_log = os.path.join(BASEDIR, "activity.log")
MONTHLY = "conso_par_mois"
MONTHLY_json = os.path.join(BASEDIR, MONTHLY + ".json")

# command line commands
CMD_Fetch = "fetch"
CMD_Sensor = "sensor"
CMD_Sensor_Nolog = "sensor_nolog"
CMD_Delete = "delete"

UNKNOWN = {'kwh':-1, 'mcube':-1}
ZERO = {'kwh':0, 'mcube':0}

def dtostr(date):
# Date formatting, like in data returned from GRDF
    return date.strftime("%d/%m/%Y")

def mtostr(date):
# month formatting, like in data returned from GRDF
    return date.strftime("%m/%Y")


def get_yesterday_conso(res, writelog):
#   extraction de la consommation de la veille
    yesterday = datetime.date.today() - relativedelta(days=1)
    try:
        conso = res.get(dtostr(yesterday), UNKNOWN)
        if writelog:
            logging.info("returning conso: " + str(conso))
    except Exception as exc:
        logging.error("Invalid daily data format found: " + str(exc))
        conso = UNKNOWN
    return conso

# Export the JSON file for daily consumption
def export_daily_values(res):
    with open(DAILY_json, 'w') as outfile:
        json.dump(res, outfile)

def get_monthly_conso(res, offset) -> dict:
    # aussi la consommation mensuelle arrive avec un jour de retard
    strMonth = datetime.date.today() - relativedelta(days=1) - relativedelta(months=offset)
    try:
        conso = res.get(mtostr(strMonth), ZERO)
        return conso
    except Exception as exc:
        return ZERO
    return retval

def export_monthly_values(res):
#   Export the JSON file of monthly consumption
#   check that we have at more than one value in array
#   otherwise, we may lose the previous monthly consumption
    if len(res) > 1:
        with open(MONTHLY_json, 'w') as outfile:
            json.dump(res, outfile)

def add_daily_log():
    logging.basicConfig(filename=DAILY_json_log, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
#   set up logging to extra file
    #logToFile = logging.FileHandler(DAILY_json_log)
    #logToFile.level = logging.INFO
    #formatter = logging.Formatter('%(asctime)s %(message)s',"%Y-%m-%d %H:%M:%S")
    #logToFile.setFormatter(formatter)
    #logging.getLogger('').addHandler(logToFile)

def fetch_data():
    """
    get data from GRDF
    write daily and monthly result to json files
    """
    add_daily_log()

    if len(sys.argv) < 6:
        logging.error(f"Pas assez de paramètres sur la ligne de commande ({len(sys.argv) - 1} au lieu de 3)")
        return False

    # we transfer login info in base64 encoded form to avoid any interpretation of special characters
    try:
        user_bytes = base64.b64decode(sys.argv[2])
        USERNAME = user_bytes.decode("utf-8")
        pwd_bytes = base64.b64decode(sys.argv[3])
        PASSWORD = pwd_bytes.decode("utf-8")
    except Exception as exc:
        logging.error(f"Cannot b64decode username ({sys.argv[2]}) or password ({sys.argv[3]}): " + str(exc))
        return False

    try:
        # logging.info(f"logging in as {USERNAME}, {PASSWORD}...")
        token = gazpar.login(USERNAME, PASSWORD)
        # logging.info("logged in successfully!")

        # logging.info("retrieving data...")
        today = datetime.date.today()

        # 12 months ago - today
        res_month = gazpar.get_data_per_month(token, dtostr(today - relativedelta(months=2)), dtostr(today))

        # on demande la consommation d'il y a 2 jours et la veille
        # mais le résultat semble toujours inclure plus de données
        res_day = gazpar.get_data_per_day(token,
                                          dtostr(today - relativedelta(days=1)),
                                          dtostr(today - relativedelta(days=2))
                                         )
        if len(res_day) > 1 and len(res_month) > 1:
            logging.info("Received data")

            try:
                export_daily_values(res_day)
                export_monthly_values(res_month)
                print("done.")
                return True
            except Exception as exc:
                logging.info("daily/monthly conso not exported")
                logging.error(exc)
                return False
        else:
          logging.info("No data received")
 
    except gazpar.GazparLoginException as exc:
        logging.error(exc)
        print("Error occurred: " + str(exc))
        return False
    except gazpar.GazparServiceException as exc:
        logging.error(exc)
        print(str(exc))
        return False
    except Exception as e:
        logging.error(str(e))
        print("Error occurred: " + str(e))
        return False

def sensor(writelog):
    """
    get conso from json result file
    get corresponding log
    send both back to Home Assistant
    """
    dailylog = ""
    add_daily_log()
    try:
        if os.path.exists(DAILY_json):
            with open(DAILY_json, 'r') as infile:
                res_day = json.load(infile)
                conso = get_yesterday_conso(res_day, writelog)
        else:
            conso = UNKNOWN

        if os.path.exists(MONTHLY_json):
            with open(MONTHLY_json, 'r') as infile:
                res_month = json.load(infile)
                conso_m = get_monthly_conso(res_month, 0)
                conso_mm1 = get_monthly_conso(res_month, 1)
        else:
            conso_m = ZERO
            conso_mm1 = ZERO

        try:
            if os.path.exists(DAILY_json_log):
                with open(DAILY_json_log,"r") as logfile:
                    dailylog = logfile.read().splitlines()
        except:
            pass
    except Exception as e:
        conso = UNKNOWN
        conso_m = ZERO
        conso_mm1 = ZERO
        logging.error("Error reading result json file: " + str(e))
    dictRet = {
               "conso": conso['kwh'],
               "conso_m3": conso['mcube'],
               "conso_curr_month": conso_m['kwh'],
               "conso_curr_month_m3": conso_m['mcube'],
               "conso_prev_month": conso_mm1['kwh'],
               "conso_prev_month_m3": conso_mm1['mcube'],
               "log": "\r\n".join(dailylog),
               }
    print(json.dumps(dictRet))

def delete_json():
    """
    delete json result file and last log file
    to avoid the current conso be carried over to the next day
    """
    ok = True
    try:
        dictNull = {}
        dictNull[dtostr(datetime.date.today() - relativedelta(days=2))] = UNKNOWN
        export_daily_values(dictNull)
    except Exception as e:
        #logging.ERROR("error when replacing json result file: " + str(e))
        print("error when replacing json result file: " + str(e))
        ok = False
    
    PREVIOUS_LOG = os.path.join(BASEDIR, "previous.log")
    try:
        if os.path.exists(PREVIOUS_LOG):
            os.remove(PREVIOUS_LOG)
        if os.path.exists(DAILY_json_log):
            os.rename(DAILY_json_log, PREVIOUS_LOG)
    except Exception as e:
        #logging.ERROR("error when deleting result log file: " + str(e))
        print("error when deleting/renaming result log file: " + str(e))
        ok = False

    add_daily_log()
    logging.info(f"Script version {PROG_VERSION}")
    logging.info("conso set to -1 (unknown)")
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
        elif sys.argv[1] == CMD_Sensor:
            sensor(True)
        elif sys.argv[1] == CMD_Sensor_Nolog:
            sensor(False)
        elif sys.argv[1] == CMD_Delete:
            if not delete_json():
                sys.exit(1)
        else:
            print(arg_errmsg)
    else:
        print(arg_errmsg)

if __name__ == "__main__":
    main()
