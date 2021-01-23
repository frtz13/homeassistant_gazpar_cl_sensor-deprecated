#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Adapted to gaspar (C) 2018 epierre
"""Generates energy consumption JSON files from GrDf consumption data
collected via their  website (API).
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
import json
import gazpar
from dateutil.relativedelta import relativedelta
from lxml import etree
import xml.etree.ElementTree as ElementTree

USERNAME = os.environ['GAZPAR_USERNAME']
PASSWORD = os.environ['GAZPAR_PASSWORD']
BASEDIR = os.environ['BASE_DIR']
LOGFILE = os.getenv('LOG_FILE', "gazpar_ha.log")

DAILY = "export_days_values"
DAILY_json = os.path.join(BASEDIR, DAILY + ".json")
DAILY_json_log = os.path.join(BASEDIR, DAILY + ".log")

# command line commands
CMD_Fetch = "fetch"
CMD_Sensor = "sensor"
CMD_Delete = "delete"

# Date formatting 
def dtostr(date):
    return date.strftime("%d/%m/%Y")


# extraction de la consommation de la veille
def get_yesterday_conso(res):
    yesterday = datetime.date.today() - relativedelta(days=1)
    for datapoint in res:
        datJour = datetime.datetime.strptime(datapoint['time'], "%d/%m/%Y").date()
        if datJour == yesterday:
            conso = datapoint['conso']
        # Remove any invalid values
        # (they're error codes on the API side, but useless here)
            if int(conso) < 0:
                conso = "0"
            logging.info("returning conso: " + conso)
            return conso
    logging.info("yesterday's conso not found")
    return "-1"    

# Export the JSON file for daily consumption (for the past rolling 30 days)
def export_daily_values(res):
    with open(DAILY_json, 'w') as outfile:
        #open was with w+. don't understand.
        json.dump(res, outfile)

#set up logging to extra file
def add_daily_log():
    logToFile = logging.FileHandler(DAILY_json_log)
    logToFile.level = logging.INFO
    formatter = logging.Formatter('%(asctime)s %(message)s',"%Y-%m-%d %H:%M:%S")
    logToFile.setFormatter(formatter)
    logging.getLogger('').addHandler(logToFile)

# get data from GRDF
# write daily result to json file
# write connection log also to extra log file
def fetch_data():
    try:
        if os.path.exists(DAILY_json_log):
            os.remove(DAILY_json_log)
    except Exception as e:
        logging.ERROR("error when deleting old log file: " + str(e))
    add_daily_log()
    try:
        logging.info("logging in as %s...", USERNAME)
        token = gazpar.login(USERNAME, PASSWORD)
        logging.info("logged in successfully!")

        logging.info("retrieving data...")
        today = datetime.date.today()

        # on demande la consommation d'il y a 2 jours et la veille
        # mais le résultat semble toujours inclure plus de données
        res_day = gazpar.get_data_per_day(token, dtostr(today - relativedelta(days=1)), \
                                         dtostr(today - relativedelta(days=2)))
        logging.info("got data!")
        try:
            export_daily_values(res_day)
            print("done.")
            return True
        except Exception as exc:
            logging.info("daily values non exported")
            logging.error(exc)
            return False
 
    except gazpar.LinkyLoginException as exc:
        logging.error(exc)
        print("Error occurred: " + str(exc))
        return False
    except Exception as e:
        logging.error(str(e))
        print("Error occurred: " + str(e))
        return False

# get yesterday's conso from json result file
# get corresponding log
# send both to sensor
def sensor():
    lastlog = ""
    try:
        if os.path.exists(DAILY_json):
            with open(DAILY_json, 'r') as infile:
                res_day = json.load(infile)
                conso = get_yesterday_conso(res_day)
        else:
            conso = "-2"

        try:
            if os.path.exists(DAILY_json_log):
                with open(DAILY_json_log,"r") as lastlogfile:
                    lastlog = lastlogfile.read()
        except:
            pass
    except Exception as e:
        conso = "-3"
        logging.error("Error reading result json file: " + str(e))
    dictRet = {"conso": str(conso), "log":lastlog.rstrip()};
    print(json.dumps(dictRet))

# delete json result file and last log file
# useful to avoid the current conso be carried over to the next day
# in case the sensor gets updated just before midnight (by a H.A. restart, for ex.) 
def delete_json():
    try:
        listNull = []
        listNull.append({'conso': '0', 'time': dtostr(datetime.date.today() - relativedelta(days=2)) })
        export_daily_values(listNull)
        #if os.path.exists(DAILY_json):
        #    os.remove(DAILY_json)
    except Exception as e:
        logging.ERROR("error when replacing json result file: " + str(e))
    try:
        if os.path.exists(DAILY_json_log):
            os.remove(DAILY_json_log)
    except Exception as e:
        logging.ERROR("error when deleting result log file: " + str(e))
    add_daily_log()
    logging.info("set 'conso' to unknown")
    print("done.")

# Main script 
def main():
    # we log to file and to a string which we include in the json result
    logging.basicConfig(filename=BASEDIR + "/" + LOGFILE, format='%(asctime)s %(message)s', level=logging.INFO)

    arg_errmsg = "use one of the following command line argugmnts: {}, {} or {}".format(CMD_Fetch, CMD_Sensor, CMD_Delete )
    if len(sys.argv) > 1:
        if sys.argv[1] == CMD_Fetch:
            if not fetch_data():
                sys.exit(1)
        elif sys.argv[1] == CMD_Sensor:
            sensor()
        elif sys.argv[1] == CMD_Delete:
            delete_json()
        else:
            print(arg_errmsg)
    else:
        print(arg_errmsg)

if __name__ == "__main__":
    main()
