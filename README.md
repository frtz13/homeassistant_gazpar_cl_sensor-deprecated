# homeassistant_gazpar_cl_sensor

## Objectif

L'objectif est de récupérer la consommation journalière de gaz (en kWh et en m<sup>3</sup>) et de le représenter sous forme d'un diagramme à barres d'un *sensor* dans Home Assistant, chaque barre correspondant à la consommation de la veille.

<img title="" src="./img/conso-graph.png" alt="Graphique de la consommation" data-align="center">

## Principe de fonctionnement

L'intégration dans Home Assistant nécessitera un peu de patience et nous fera visiter quelques aspects de ce système.

La consommation est représentée sous forme d'un *Command line sensor* dont la mise à jour est provoquée par une *Automatisation*. Ainsi nous maîtrisons le moment de connexion à l'espace client GRDF, et nous évitons de l'interroger inutilement à propos de la consommation de la veille, sachant qu'elle n'est disponible qu'à partir de l'après-midi, ou même encore plus tard. En tout cas, il en est ainsi pour la mienne.

La récupération de la consommation se déroule de la manière suivante:

- Dans l'après-midi, la commande *gazpar_ha.sh fetch* effectuera une connexion à l'espace client GRDF et enregistre les consommations journalières des jours passés dans le fichier *export_days_values.json*, ansi que les consommations mensuelles dans le fichier *export_months_values.json*.

- Ensuite, la commande *gazpar_ha.sh sensor* va extraire la consommation de la veille, du mois courant et du mois précédent de ces fichiers. C'est cette commande qui alimente le *Command line sensor* et qui lui fournit la consommation de la veille (entre autres).

- Un peu avant minuit, nous effaçons le fichier des consommations journalières, puis lançons une *Automatisation* remet le *Sensor* à la valeur "inconnu" (-1).

Ainsi, chaque jour, notre *Sensor* aura cette valeur jusqu'à la récupération de la consommation de veille, qu'il conservera jusqu'à peu avant minuit.

Nous contournons une difficulté: l'interrogation de l'espace client GRDF dure souvent plus longtemps que 10 secondes. Or, Home Assistant abandonne l'attente au bout de 10 secondes, et rate ainsi le résultat. 

## Installation

Créer un dossier *gazpar* dans le dossier *config* de Home Assistant (là, où se trouve le fichier *configuration.yaml*).

NB: ce dossier est à la fois accessible de l'intérieur du conteneur Home Assistant, et depuis la machine hôte. Il est ainsi possible d'y accéder par *scp* ou par *Samba* pour y copier des fichiers, si vous avez installé cette extension. 

Placez-vous dans ce dossier, et commencez à télécharger le premier fichier:

```
wget https://raw.githubusercontent.com/frtz13/homeassistant_gazpar_cl_sensor/master/gazpar.py
```

Faites de même avec:

- gazpar_ha.py

- gazpar_ha.sh

- requirements.txt

- gazpar_modele.cfg

Rendre gazpar_ha.sh exécutable:

```
chmod +x gazpar_ha.sh
```

NB: selon votre contexte de travail, il est possible qu'il soit nécessaire de faire précéder certaines commandes par "sudo".

## Mise à jour

Si vous utilisez déjà une version précédente du gazpar_cl_sensor:

- Remplacez les fichiers qui ont été modifiés.

- Complétez et modiez les définitions des Sensors dans Home Assistant.

- (Recommandé) Installez Apex Graph card.

## Paramétrer l'accès à l'espace client GRDF

Tout d'abord, il faudra créer un espace client chez GRDF, si cela n'est pas déjà fait, et s'y rendre, afin d'accepter les CGV.

Faire une copie de *gazpar_modele.cfg* et la nommer *gazpar.cfg*. Ensuite éditer ce nouveau fichier (avec nano, ou avec un éditeur dans Home Assistant, cf. ci-dessous) et paramétrer:

    GAZPAR_USERNAME="votre@adresse.email"
    GAZPAR_PASSWORD="password"

## Intégration dans Home Assistant

### Définition du *Command Line Sensor* et des *Shell commands*

Si vous n'avez pas encore installé un éditeur pour modifier le fichier *configuration.yaml* de Home Asssitant, c'est le moment. A partir du Add-on Store du Superviseur de Home Assistant, installez "File editor" ou "Visual Studio Code".

Dans *configuration.yaml*, ajouter:

```
sensor:
  - platform: command_line
    name: GRDF consommation gaz
    command: "/config/gazpar/gazpar_ha.sh sensor"
    scan_interval: 100000000
    unit_of_measurement: "kWh"
    json_attributes:
      - conso_curr_month
      - conso_prev_month
      - log
    value_template: '{{ value_json.conso }}'

  - platform: command_line
    name: GRDF consommation gaz (m3)
    command: "/config/gazpar/gazpar_ha.sh sensor_nolog"
    scan_interval: 100000000
    unit_of_measurement: "m3"
    json_attributes:
      - conso_curr_month_m3
      - conso_prev_month_m3
      - log
    value_template: '{{ value_json.conso_m3 }}'

  - platform: template
    sensors:
      grdf_conso_curr_month:
        friendly_name: "Consommation gaz mois courant"
        unit_of_measurement: "kWh"
        value_template: "{{ state_attr('sensor.grdf_consommation_gaz', 'conso_curr_month') }}"
      grdf_conso_prev_month:
        friendly_name: "Consommation gaz mois précédent"
        unit_of_measurement: "kWh"
        value_template: "{{ state_attr('sensor.grdf_consommation_gaz', 'conso_prev_month') }}"
      grdf_conso_curr_month_m3:
        friendly_name: "Consommation gaz mois courant (m3)"
        unit_of_measurement: "m3"
        value_template: "{{ state_attr('sensor.grdf_consommation_gaz_m3', 'conso_curr_month_m3') }}"
      grdf_conso_prev_month_m3:
        friendly_name: "Consommation gaz mois précédent (m3)"
        unit_of_measurement: "m3"
        value_template: "{{ state_attr('sensor.grdf_consommation_gaz_m3', 'conso_prev_month_m3') }}"
```

```
shell_command:
    grdf_get_data: '/config/gazpar/gazpar_ha.sh fetch'
    grdf_delete_data: '/config/gazpar/gazpar_ha.sh delete'
```

NB: si *configuration.yaml* contient déjà une rubrique "sensor:", ne créez pas une nouvelle rubrique de ce nom, mais ajoutez les définitions "sensor" à la rubrique existante. Idem pour la partie *shell_command*.

NB2: L'appel de *gazpar_ha.sh* avec l'option sensor_nolog a pour but d'éviter d'ajouter trop de lignes dans le fichier log, visible dans les Attributs du Sensor.

Ensuite, menu Configuration / Contrôle du serveur:  vérifier la configuration (très important de le faire chaque fois!), et si tout es ok, redémarrer Home Assistant.

### Essais

Dans Home Assistant, rendez-vous dans Outils de développement / SERVICES, sélectionner le service *shell_command.grdf_delete_data* puis appuyez sur "Call SERVICE". Cela installera d'éventuels bibliothèques manquantes.

Ensuite, faites de même avec le service *shell_command.grdf_get_data*.Retournez à la ligne de commande et examinez le contenu de votre dossier *gazpar*.

Si tout va bien, s'y trouvent des nouveaux fichiers: *conso_par_jour.json* et *activity.log*, *conso_par_mois.json*. Vous pouvez consulter votre consommation des jours passés par la commande *cat export_days_values.json*.

Si aucun nouveau fichier n'est présent: vérifiez qu'il n'y a pas d'erreur au niveau du nom du dossier (écriture en majuscules/minuscules compte!).

Si vous avez obtenu le fichiers *log* mais pas le fichier *json*: lisez le log; peut-être un problème avec les identifiants pour accéder à l'espace client GRDF, ou que l'accès à l'espace n'a pas permis de récupérer des données de consommation (dans ce cas, on trouve la mention "No results in data" dans le log). Dans ce cas, exécutez le SERVICE une nouvelle fois dans Home Assistant.

Lançons maintenant la mise à jour de notre *sensor*: rendez-vous dans Outils de développement / SERVICES, sélectionnez le service *homeassistant.update_entity* puis l'Entité *sensor.grdf_consommation_gaz*, puis appuyez sur "Call SERVICE". Puis regardez dans Outils de développement / ETATS, si votre Entité *sensor.grdf_consommation_gaz* a bien été mis à jour avec la consommation de la veille. Si elle porte la valeur -1, cela signifie que la consommation de la veille n'est pas encore disponible (vérifiez!).

### Automatisation de la lecture de la consommation de la veille

Pour rendre la connexion à l'espace client automatique, nous ajoutons une *Automatisation* dans Home Assistant (Configuration / Automatisations, commencer par une Automatisation vide):

- Nom: *GRDF get data*, Mode: Unique

- Déclencheur: type: Modèle de temps, Heures: 18, Minutes: /10, Secondes: 0
  ce qui signifie: entre 18 et 19 heures, déclencher cette *Automatisation* toutes les 10 minutes.

- Conditions: type: Valeur numérique, Entité: sensor.grdf_consommation_gaz, en dessous de: -0.5

- Actions:
  
  - type *Appeler un service*: shell_command.grdf_get_data
  
  - type: *Délai*, valeur: 00:02:00
  
  - type: *Appeler un service*, service: *homeassistant.update_entity*: *sensor.grdf_consommation_gaz* et *sensor.grdf_consommation_gaz_m3*.

Quelques remarques:

- Vous pouvez par la suite ajouter à cette Automation d'autres Triggers de type Time ou Time Pattern.

- Grâce à la "condition", cette Automation ne se déclenchera plus dès que nous aurons obtenu la consommation de la veille.

- Le délai dans les Actions laissera un peu de temps à l'action précédente de se terminer, même si Home Assistant perd la patience au bout de 10s.

Une chose est encore à faire: peu avant minuit, la valeur du *sensor* doit être remis à l'état *inconnu*. Donc, une autre Automatisation:

- Nom: *GRDF reset*, Mode: Unique

- Déclencheur: type *Heure*, à: 23:57

- Actions:
  
  - type *Appeler un service*, *shell_command.grdf_delete_data*
  
  - type: Délai, valeur: 00:01:00
  
  - type *Appeler un service*, service: *homeassistant.update_entity:* *sensor.grdf_consommation_gaz* et *sensor.grdf_consommation_gaz_m3*.

### Le graphique

Pour la présentation, nous utiliserons la "Apex graph card"

Pour la présentation, nous utiliserons la "Apex graph card" ([[GitHub - RomRider/apexcharts-card:  A Lovelace card to display advanced graphs and charts based on ApexChartsJS for Home Assistant](https://github.com/RomRider/apexcharts-card)]).

Son installation se résume grosso-modo à:

- télécharger *apexcharts-card.js* et le placer dans le dossier /config/www

- dans Home Assistant, se rendre dans Configuration / Tableaux de bord Lovelace, onglet Ressources. Click sur "+" puis saisir la URL "/local/apexcharts-card.js" et préciser le type *Javascript module*.

Enfin, dans votre tableau de bord, ajoutez y une carte de type *Personnalisé: ApexCharts Card*, Dans la configuration de la carte, copiez/collez te texte suivant:

```
type: 'custom:apexcharts-card'
graph_span: 10d1s
span:
  end: day
header:
  show: true
  title: Consommation gaz
  show_states: false
  standard_format: true
series:
  - entity: sensor.grdf_consommation_gaz
    type: column
    offset: +1day
    show:
      name_in_header: false
    group_by:
      func: max
      duration: 1d
apex_config:
  yaxis:
    min: 0
```

--

Un grand merci à [Emmanuel](https://github.com/empierre) et à [Fabien](https://github.com/beufanet) pour l'élaboration du script d'accès à l'espace client GRDF.
