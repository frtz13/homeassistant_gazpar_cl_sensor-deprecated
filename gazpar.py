# adapted from cyprieng / gazpar-home-assistant (many thanks !)

# adapted by: frtz13
# - removed retries (done by Automations in H.A.)
# - changed return value
# - added login success check and exception
# - added simple check that we get some meaningful data

import datetime
import requests
import time
import json

class GazparLoginException(Exception):
    """Thrown if a login error was encountered"""
    pass


class Gazpar:
    def __init__(self, username, password, pce):
        """Init gazpar class

        Args:
            username: username
            password: password
            pce: Pce identifier
        """
        self.username = username
        self.password = password
        self.pce = pce

    def get_consumption(self):
        session = requests.Session()

        # Login
        login_response = session.post('https://login.monespace.grdf.fr/sofit-account-api/api/v1/auth', data={
            'email': self.username,
            'password': self.password,
            'capp': 'meg',
            'goto': 'https://sofa-connexion.grdf.fr:443/openam/oauth2/externeGrdf/authorize?response_type=code&scope=openid%20profile%20email%20infotravaux%20%2Fv1%2Faccreditation%20%2Fv1%2Faccreditations%20%2Fdigiconso%2Fv1%20%2Fdigiconso%2Fv1%2Fconsommations%20new_meg&client_id=prod_espaceclient&state=0&redirect_uri=https%3A%2F%2Fmonespace.grdf.fr%2F_codexch&nonce=skywsNPCVa-AeKo1Rps0HjMVRNbUqA46j7XYA4tImeI&by_pass_okta=1&capp=meg'
        })

        # check login success
        login_result = json.loads(login_response.text)
        if ("status" in login_result) and ("error" in login_result) and (login_result["status"] >= 400):
            raise GazparLoginException(f"{login_result['error']} ({login_result['status']})")
        if ("state" in login_result) and (login_result["state"] != "SUCCESS"):
            raise GazparLoginException(login_result["error"])

        # First request never returns data
        url = 'https://monespace.grdf.fr/api/e-conso/pce/consommation/informatives?dateDebut={0}&dateFin={1}&pceList%5B%5D={2}'.format(
            (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
            datetime.datetime.now().strftime('%Y-%m-%d'),
            self.pce)
        #url = 'https://monespace.grdf.fr/api/e-conso/pce/consommation/publiees?dateDebut={0}&dateFin={1}&pceList%5B%5D={2}'.format(
        #    "2021-10-01",
        #    "2021-11-01",
        #    self.pce)
#        print(url)
        session.get(url) # first try, never returns data
        # now get data
        response = session.get(url)
        try:
            resp_json = response.json()
            if self.pce in resp_json:
                return response.json()[self.pce]
            else:
                raise Exception("No Relevé in response")
        except Exception as exc:
            raise Exception("Invalid data received")
