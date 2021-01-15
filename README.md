# homeassistant_gaspar_cl_sensor
Récuperer la consommation journalière de gaz depuis l'espace client de GRDF et l'envoyer à Home Assistant
!!! Travail en cours !!!

L'intégration dans Home Assistant est faite sous forme d'un 'Command Line sensor'.
Un soin particulier a été apporté de maîtriser le moment et la fréquence de l'interrogation de l'espace client de GRDF.


## modules à installer

    sudo apt-get install python3-dateutil python3-requests python3-lxml

### paramétrer login/pass/id

    nano domoticz_gaspar.cfg

and change:

    GASPAR_USERNAME="nom.prenom@mail.com"
    GASPAR_PASSWORD="password"


## testing before launch

Manually launch

    ./domoticz_gaspar.sh   or .bat for windows

N.B. If login is not ok, you'll get a nodejs error on console for data will be missing (will be changed).

Then check the login credential if they are ok:

    domoticz_gaspar.log

If this is good, you'll get several json files in the directory

