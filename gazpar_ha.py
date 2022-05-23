#!/usr/bin/env python3
# Adapted to gaspar (C) 2018 epierre
# Adapted to Home Assistant by frtz13
# homeassistant_gazpar_cl_sensor

"""
Returns energy consumption data from GRDF consumption data
collected via their website (API).
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

import base64
import json
import logging
import os
import sys

import gazpar

PROG_VERSION = "2022.03.30"

BASEDIR = os.environ["BASE_DIR"]

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
KEY_coeffConversion = "coeffConversion"
KEY_NEWDATA = "new_data"
JG_initial = "1970-01-01"


def export_daily_values(res):
    """Export the JSON file for daily consumption"""
    with open(DAILY_json, "w") as outfile:
        json.dump(res, outfile)


def add_daily_log():
    logging.basicConfig(
        filename=DAILY_json_log,
        format="%(asctime)s %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        level=logging.INFO,
    )


#   set up logging to extra file
# logToFile = logging.FileHandler(DAILY_json_log)
# logToFile.level = logging.INFO
# formatter = logging.Formatter('%(asctime)s %(message)s',"%Y-%m-%d %H:%M:%S")
# logToFile.setFormatter(formatter)
# logging.getLogger('').addHandler(logToFile)


def read_releve_from_file():
    try:
        if os.path.exists(DAILY_json):
            with open(DAILY_json) as infile:
                return json.load(infile)
        else:
            return None
    except Exception as e:
        logging.error(f"Error reading releve json file: {e}")
        return None


def fetch_data():
    """
    get data from GRDF
    write daily and monthly result to json files
    """
    add_daily_log()

    if len(sys.argv) < 7:
        logging.error(
            f"Pas assez de paramètres sur la ligne de commande"
            f" ({len(sys.argv) - 1} au lieu de 6)"
        )
        return False

    # Use base64 encoded form to transfer log information
    # to avoid any interpretation of special characters
    try:
        user_bytes = base64.b64decode(sys.argv[2])
        USERNAME = user_bytes.decode("utf-8")
        pwd_bytes = base64.b64decode(sys.argv[3])
        PASSWORD = pwd_bytes.decode("utf-8")
        PCE = sys.argv[4]
    except Exception as exc:
        logging.error(
            f"Cannot b64decode username ({sys.argv[2]})"
            f" or password ({sys.argv[3]}): {exc}"
        )
        return False

    # Get saved consumption result and date,
    # so we know when we will get new values
    daily_values = read_releve_from_file()
    COEFF_initial = 10.99
    if daily_values is None:
        old_date = JG_initial
        old_index_m3 = 0
        old_index_kWh = 0
        old_coeff = COEFF_initial
    else:
        old_date = daily_values[KEY_DATE]
        if KEY_INDEX_M3 in daily_values:
            old_index_m3 = daily_values[KEY_INDEX_M3]
        else:
            old_index_m3 = 0
        if KEY_INDEX_kWh in daily_values:
            old_index_kWh = daily_values[KEY_INDEX_kWh]
        else:
            old_index_kWh = 0
        if KEY_coeffConversion in daily_values:
            old_coeff = daily_values[KEY_coeffConversion]
        else:
            old_coeff = COEFF_initial
    try:
        grdf_client = gazpar.Gazpar(USERNAME, PASSWORD, PCE)
        result_json = grdf_client.get_consumption()
    except gazpar.GazparLoginException as exc:
        strErrMsg = "[Login error] " + str(exc)
        logging.error(strErrMsg)
        print("Error occurred: " + strErrMsg)
        return False
    except ConnectionError:
        strErrMsg = "[Error] Cannot connect"
        logging.error(strErrMsg)
        print(strErrMsg)
        return False
    except gazpar.GazparInvalidDataException as exc:
        strErrMsg = "[Error: Invalid data] "
        if len(str(exc)) == 0:
            strErrMsg += "Empty response"
        else:
            try:
                INV_DATA = "invalid_data.txt"
                with open(os.path.join(BASEDIR, INV_DATA), "w") as f:
                    f.write(str(exc))
                strErrMsg += f"Written to {INV_DATA}"
            except Exception:
                strErrMsg += "Failed to write invalid data to file"
        logging.error(strErrMsg)
        print(strErrMsg)
        return False
    except Exception as exc:
        strErrMsg = "[Error] " + str(exc)
        logging.error(strErrMsg)
        print(strErrMsg)
        return False

    JG = "journeeGaziere"
    RELEVES = "releves"
    EN_CONSO = "energieConsomme"
    INDEX_FIN = "indexFin"
    QUAL_RELEVE = "qualificationReleve"

    new_index_kWh = old_index_kWh
    try:
        if len(result_json[RELEVES]) == 0:
            strErrMsg = "Aucun relevé reçu"
            logging.error(strErrMsg)
            print(str(strErrMsg))
            return False

        # parcourt des relevés, au cas où un relevé
        # aurait été manqué depuis la lecture précédente
        absDonn = False
        missing = True  # détecter absence de relevés depuis > 7 jrs
        jrs = 0
        for r in reversed(result_json[RELEVES]):
            if r[JG] is None:
                continue
            if r[JG] <= old_date:
                missing = False
                break
            if r[EN_CONSO] is None:
                absDonn = True
            else:
                new_index_kWh += r[EN_CONSO]
            jrs += 1
            # au commencement, nous ne prenons que le dernier relevé
            if old_date == JG_initial:
                missing = False
                break

        dictLatest = result_json[RELEVES][-1]

        # si la journée gazière la plus récente est une sans relevé,
        # nous attendons une avec relevé
        if dictLatest[INDEX_FIN] is None:
            if dictLatest[QUAL_RELEVE] is None:
                strErrMsg = "Absence de données"
            else:
                strErrMsg = dictLatest[QUAL_RELEVE]
            logging.error(strErrMsg)
            print(str(strErrMsg))
            return False

        try:
            coeff = dictLatest["coeffConversion"]
            if coeff is None:
                coeff = old_coeff
        except Exception:
            coeff = old_coeff

        # Pour une journée gazière sans relevé,
        # calcul de l'évolution de l'index_kWh avec l'évolution de l'index_m3
        # idem si la récup de relevés précédente remonte à plus de 7 jrs
        absDonnMsg = ""
        missingMsg = ""
        if absDonn or missing:
            new_index_kWh = old_index_kWh + round(
                (dictLatest[INDEX_FIN] - old_index_m3) * coeff
            )
            if absDonn:
                absDonnMsg = ", absDonn"
            if missing:
                missingMsg = ", miss"

        daily_values = {
            KEY_DATE: dictLatest[JG],
            KEY_CONSO_kWh: dictLatest["energieConsomme"],
            KEY_CONSO_m3: dictLatest["volumeBrutConsomme"],
            KEY_INDEX_kWh: new_index_kWh,
            KEY_INDEX_M3: dictLatest["indexFin"],
            KEY_coeffConversion: coeff,
            KEY_NEWDATA: True,
        }
    except Exception as exc:
        strErrMsg = "[No data received] " + str(exc)
        logging.error(strErrMsg)
        print(str(strErrMsg))
        return False

    try:
        if (daily_values[KEY_DATE] is None) or (
            daily_values[KEY_DATE] == old_date
        ):
            logging.info("No new data")
        else:
            logging.info(
                "Received data"
                + (f" ({jrs} j{absDonnMsg}{missingMsg})" if jrs > 1 else "")
            )
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
                with open(DAILY_json_log) as logfile:
                    dailylog = "\r\n".join(logfile.read().splitlines())
        except Exception:  # nosec
            pass

        daily_values["log"] = dailylog
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
        daily_values = {
            KEY_DATE: JG_initial,
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
        # logging.ERROR("error when replacing json result file: " + str(e))
        print("error when replacing releve file: " + str(e))
        ok = False

    PREVIOUS_LOG = os.path.join(BASEDIR, "previous.log")
    try:
        if os.path.exists(PREVIOUS_LOG):
            os.remove(PREVIOUS_LOG)
        if os.path.exists(DAILY_json_log):
            os.rename(DAILY_json_log, PREVIOUS_LOG)
    except Exception as e:
        # logging.ERROR("error when deleting result log file: " + str(e))
        print("error when deleting/renaming log file: " + str(e))
        ok = False

    add_daily_log()
    logging.info(f"Script version {PROG_VERSION} / {gazpar.VERSION}")
    logging.info("reset daily conso")
    print("done.")
    return ok


# Main script
def main():
    # we log to file and to a string which we include in the json result
    # logging.basicConfig(filename=BASEDIR + "/" + LOGFILE,
    #                     format='%(asctime)s %(message)s', level=logging.INFO)

    arg_errmsg = (
        f"Use one of the following command line arguments:"
        f" {CMD_Fetch}, {CMD_Sensor}, {CMD_Sensor_Nolog}"
        f" or {CMD_Delete}"
    )
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
