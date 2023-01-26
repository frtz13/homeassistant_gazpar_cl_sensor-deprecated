# homeassistant_gazpar_cl_sensor

A python script that gets gaz consumption data from GRDF, the French
natural gaz distribution company. As this is interesting only for people
living in France, this documentation is written in French.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=4 --minlevel=2 -->

- [Objectif](#objectif)
- [Principe de fonctionnement](#principe-de-fonctionnement)
- [Installation](#installation)
- [Mise à jour](#mise-%C3%A0-jour)
- [Paramétrer l'accès à l'espace client GRDF](#param%C3%A9trer-lacc%C3%A8s-%C3%A0-lespace-client-grdf)
- [Intégration dans Home Assistant](#int%C3%A9gration-dans-home-assistant)
  - [Définition du Command Line Sensor, Shell commands etc.](#d%C3%A9finition-du-command-line-sensor-shell-commands-etc)
  - [Essais](#essais)
  - [Automatisation de la lecture de la consommation de la veille](#automatisation-de-la-lecture-de-la-consommation-de-la-veille)
  - [Le graphique](#le-graphique)
  - [Encore quelques remarques "en vrac":](#encore-quelques-remarques-en-vrac)
    - [Suivre l'exécution du script](#suivre-lex%C3%A9cution-du-script)
    - [Messages dans activity.log](#messages-dans-activitylog)
    - [Une autre façon d'enregistrer les paramètres de connexion à l'espace client GRDF](#une-autre-fa%C3%A7on-denregistrer-les-param%C3%A8tres-de-connexion-%C3%A0-lespace-client-grdf)

<!-- mdformat-toc end -->

## Actualité

Depuis le 19/1/2023, l'accès à l'espace client passe systématiquement par une vérification par reCaptcha, ce qui le rend inaccessible à des traitements automatisés comme celui-ci.

## Objectif

L'objectif est de récupérer la consommation journalière de gaz (en kWh et
en m<sup>3</sup>) et de la représenter sous forme d'un diagramme à barres
dans Home Assistant, chaque barre correspondant à la consommation de
l'avant-veille. La consommation peut également être intégrée dans le
Tableau de bord Energie de Home Assistant.

<img title="" src="./img/ha_energy_gas.png" alt="Graphique de consommation de gaz dans le Tableau de bord Energy de Home Assistant" data-align="center">

<img title="" src="./img/conso-graph.png" alt="Graphique de la consommation" data-align="center">

## Principe de fonctionnement

La consommation est représentée sous forme d'un *Command line sensor* dont
la mise à jour est provoquée par une *Automatisation*. Ainsi nous
maîtrisons le moment et la fréquence de connexion à l'espace client GRDF,
et nous évitons de l'interroger inutilement à propos de la consommation,
sachant qu'elle n'est disponible que dans la soirée. En tout cas, il en est
ainsi pour la mienne. Notons qu'actuellement les relevés de consommation
sont publiées avec deux jours de retard, et qu'il s'agit en conséquence
chaque fois de la consommation de l'avant-veille.

La récupération de la consommation se déroule de la manière suivante:

- Dans la soirée, la commande *gazpar_ha.sh fetch* effectue une connexion à
  l'espace client GRDF, récupère les derniers relevés publiés, extrait la
  consommation du relevé de l'avant-veille (s'il est disponible), et
  enregistre la consommation et les valeurs des indices kWh et
  m<sup>3</sup> dans le fichier *releve_du_jour.json*.

- Ensuite, un *Command line sensor* mis en oeuvre par la commande
  *gazpar_ha.sh sensor* rend ces informations accessibles à Home Assistant.

- Un peu avant minuit, la commande *gazpar_ha.sh delete* effacera les
  consommations journalières de ce fichier, et un autre appel *gazpar_ha.sh
  sensor* remet les *Sensors* de la consommation journalière à la valeur
  *unavailable*.

## Installation

Créez un dossier *gazpar* dans le dossier *config* de Home Assistant (là,
où se trouve le fichier *configuration.yaml*).

Placez-vous dans ce dossier, et commencez à télécharger le premier fichier:

```shell
wget https://raw.githubusercontent.com/frtz13/homeassistant_gazpar_cl_sensor/master/gazpar.py
```

Faites de même avec:

- gazpar_ha.py

- gazpar_ha.sh

- requirements.txt

Vous pouvez utiliser d'autres méthodes pour effectuer cette opération, par
ex.: télécharger le contenu du Repository sous forme d'un fichier .zip,
extraire les fichiers désignés, et les transférer dans ce dossier avec la
commande Upload de File Editor. Ou encore y accéder par un partage Samba.

Rendez gazpar_ha.sh exécutable:

```shell
chmod +x gazpar_ha.sh
```

NB: selon votre contexte de travail, il est possible qu'il soit nécessaire
de faire précéder certaines commandes par "sudo".

Cette opération peut également être effectuée avec cette commande Execute
Shell Command de File Editor: `chmod +x ./gazpar/gazpar_ha.sh`

## Mise à jour

Si vous utilisez déjà une version précédente du gazpar_cl_sensor:

- Remplacez les fichiers qui ont été modifiés.

- Passez le reste de cet article en revue et complétez et modifiez les
  définitions des Sensors etc. dans Home Assistant. En particulier, si vous passez d'une version précédente à la version 2022.09.21 de gazpar_ha.py, modifiez l'Automatisation "GRDF get data".

- Vous pouvez supprimer les fichiers devenus inutiles: gazpar_ha.cfg,
  conso_par_jour.json, conso_par_mois.json.

## Paramétrer l'accès à l'espace client GRDF

Tout d'abord, il faudra créer un espace client chez GRDF, si cela n'est pas
déjà fait, et s'y rendre, afin d'accepter les CGV. Pour ce faire, vous avez besoin du PCE de votre raccordement, que vous pouvez trouver dans votre facture de votre fournisseur de gaz, par ex.

Si vous n'avez pas encore installé un éditeur de texte pour modifier des
fichiers de configuration de Home Assistant, c'est le moment. A partir de la
*Boutique des Modules complémentaires (Add-ons)* Home Assistant, installez "File editor" ou "Visual Studio Code".

Inscrivez votre nom utilisateur, mot de passe et votre PCE dans `secrets.yaml`:

```yaml
grdf_user: "votre@adresse.email"
grdf_pwd: "password"
grdf_pce: "votre_pce"
```

## Intégration dans Home Assistant

### Définition du *Command Line Sensor*, *Shell commands* etc.

Dans *configuration.yaml*, ajouter:

```yaml
sensor:
  - platform: command_line
    name: GRDF consommation gaz
    command: "/config/gazpar/gazpar_ha.sh sensor"
    scan_interval: 100000000
    unit_of_measurement: "kWh"
    json_attributes:
      - conso_m3
      - index_kWh
      - index_m3
      - coeffConversion
      - date
      - log
    value_template: '{{ value_json.conso_kWh }}'

# Un de ces Sensors permettra d'ajouter la consommation au Tableau de bord Energie
template:
  - sensor:
      - name: "Gas consumption index (m³)"
        unit_of_measurement: "m³"
        device_class: "gas"
        state_class: "total_increasing"
        state: "{{ state_attr('sensor.grdf_consommation_gaz', 'index_m3') }}"

      - name: "Gas consumption index (kWh)"
        unit_of_measurement: "kWh"
        device_class: "energy"
        state_class: "total_increasing"
        state: "{{ state_attr('sensor.grdf_consommation_gaz', 'index_kWh') }}"

# Ce Sensor est optionnel
      - name: "GRDF consommation gaz (m³)"
        unit_of_measurement: "m³"
        device_class: "gas"
        state: "{{ state_attr('sensor.grdf_consommation_gaz', 'conso_m3') }}"

shell_command:
    grdf_get_data: '/config/gazpar/gazpar_ha.sh fetch  {{ states("input_text.grdf_user") | base64_encode }} {{ states("input_text.grdf_pwd") | base64_encode }}  {{ states("input_text.grdf_pce") }}'
    grdf_delete_data: '/config/gazpar/gazpar_ha.sh delete'

input_text:
  grdf_user:
    initial: !secret grdf_user
  grdf_pwd:
    initial: !secret grdf_pwd
  grdf_pce:
    initial: !secret grdf_pce
```

NB: si *configuration.yaml* contient déjà de telles rubriques, ne créez
pas de nouvelles rubriques de ce nom, mais ajoutez les définitions
à la rubrique existante.

L'attribut *date* du *Sensor GRDF consommation gaz* correspond à la
*Journée gazière* du relevé. Cette date correspond à la veille du relevé du
compteur, qui est effectuée tôt le matin. Au moment où j'écris ces lignes,
on récupère les relevés avec deux jours de retard.

Ensuite, menu Configuration / Contrôle du serveur: vérifier la
configuration (très important de le faire chaque fois!), et si tout est ok,
redémarrer Home Assistant. Un tel redémarrage est également nécessaire pour
une prise en compte de modifications des infos dans *secrets.yaml*.

A l'aide du sensor *Gas consumption index (kWh)* ou *Gas consumption index
(m<sup>3</sup>)*, vous pouvez ajouter votre consommation de gaz au Tableau
de bord Energie de Home Assistant.

Le coefficient de conversion est celui fourni par GRDF dans les relevés.

### Essais

Dans Home Assistant, rendez-vous dans Outils de développement / SERVICES,
sélectionner le service *shell_command.grdf_delete_data* puis appuyez sur
"Call SERVICE". Cela installera d'éventuelles bibliothèques PYTHON
manquantes, et devrait créer les fichiers *releve_du_jour.json*,
*activity.log*, *pip.log* et *piperror.log* dans le dossier *gazpar*.

Si aucun nouveau fichier n'est présent: vérifiez qu'il n'y a pas d'erreur
au niveau du nom du dossier (écriture en majuscules/minuscules compte!),
que vous avez bien suivi toutes les étapes de l'installation, et consultez
le log de Home Assistant.

Ensuite, appelez le service *shell_command.grdf_get_data*. Examinez à
nouveau le contenu de votre dossier *gazpar*.

Si tout va bien, les fichiers *releve_du_jour.json* et *activity.log* ont
évolués. Je vous invite de consulter le contenu de ces fichiers.

Si vous avez obtenu le fichier *activity.log* mais pas de fichier *json*:
consultez-le; il y a peut-être un problème avec les identifiants pour
accéder à l'espace client GRDF, ou que l'accès à l'espace n'a pas permis de
récupérer des données de consommation (dans ce cas, on trouve la mention
"No data received" dans le log). Exécutez le service une nouvelle fois dans
Home Assistant.

Lançons maintenant la mise à jour de notre *sensor*: rendez-vous dans
Outils de développement / SERVICES, sélectionnez le service
*homeassistant.update_entity*, puis l'Entité
*sensor.grdf_consommation_gaz*, et ensuite appuyez sur "Call SERVICE". Puis
regardez dans Outils de développement / ETATS, si votre Entité
*sensor.grdf_consommation_gaz* a bien été mise à jour avec la consommation
du relevé le plus récent disponible.

### Automatisation de la lecture de la consommation de la veille

Pour rendre la connexion à l'espace client automatique, nous ajoutons une
*Automatisation* dans Home Assistant (Configuration / Automatisations).

Commencez par une Automatisation vide, passez en mode YAML, et collez la
définition suivante:

```yaml
alias: GRDF get data
description: 'Récupérer les données de consommation'
trigger:
  - platform: time_pattern
    hours: '20'
    minutes: /30
    seconds: '00'
  - platform: time_pattern
    hours: '21'
    minutes: /30
    seconds: '00'
  - platform: time_pattern
    hours: '22'
    minutes: /30
    seconds: '00'
  - platform: time_pattern
    hours: '23'
    minutes: /10
    seconds: '00'
condition:
  - condition: state
    entity_id: sensor.grdf_consommation_gaz
    state: unavailable
action:
  - service: shell_command.grdf_get_data
  - delay:
      hours: 0
      minutes: 1
      seconds: 0
      milliseconds: 0
  - service: homeassistant.update_entity
    target:
      entity_id:
        - sensor.grdf_consommation_gaz
mode: single
```

Quelques remarques:

- Grâce à la "condition", cette Automation ne se déclenchera plus, dès que
  nous aurons obtenu des données de consommation.

- Le délai dans les Actions laissera un peu de temps à l'Action précédente
  de se terminer, même si Home Assistant perd la patience au bout d'une
  minute.

Une chose est encore à faire: peu avant minuit, la valeur du *sensor* doit
être remis à l'état *unavailable*. Donc, une autre Automatisation:

```yaml
alias: GRDF reset
description: 'Effacer données de consommation journalières'
trigger:
  - platform: time
    at: '23:56'
condition: []
action:
  - service: shell_command.grdf_delete_data
    data: {}
  - delay: '00:01:00'
  - service: homeassistant.update_entity
    target:
      entity_id:
        - sensor.grdf_consommation_gaz
mode: single
```

### Le graphique

Pour la présentation, nous utiliserons la "ApexCharts Card"
(\[[GitHub - RomRider/apexcharts-card: A Lovelace card to display advanced graphs and charts based on ApexChartsJS for Home Assistant](https://github.com/RomRider/apexcharts-card)\]).

Son installation se résume grosso-modo à:

- télécharger *apexcharts-card.js* et le placer dans le dossier
  `/config/www`

- dans Home Assistant, se rendre dans Configuration / Tableaux de bord
  Lovelace, onglet Ressources. Click sur "+" puis saisir la URL
  "/local/apexcharts-card.js" et préciser le type *Javascript module*.

Enfin, dans votre tableau de bord, ajoutez y une carte de type
*Personnalisé: ApexCharts Card*, Dans la configuration de la carte,
copiez/collez te texte suivant:

```yaml
type: 'custom:apexcharts-card'
graph_span: 12d
span:
  end: day
header:
  show: true
  title: Consommation gaz (kWh)
  show_states: false
  standard_format: true
yaxis:
  - min: 0
    decimals: 0
    apex_config:
      forceNiceScale: true
series:
  - entity: sensor.grdf_consommation_gaz
    type: column
    offset: +2day
    float_precision: 0
    show:
      name_in_header: false
    group_by:
      func: max
      duration: 1d
```

### Encore quelques remarques "en vrac":

A propos de l'index_kWh: dans ses relevés, GRDF publie un index_m3, mais
pas un index_kWh. Pour fabriquer celui-ci, le script cumule les valeurs de
l'énergie consommée journalière (celle-ci est publiée dans les relevés) au
fur et à mesure.

Quand plusieurs relevés ont été publiés depuis la dernière lecture des
données de consommation chez GRDF (soit parce que le script n'a pas été
lancé, ou parce que plusieurs relevés ont été publiés dans une même
journée), l'index_kWh cumulera l'énergie consommée de plusieurs relevés
(tous ceux après la date mémorisée dans le fichier *releve_du_jour.json*).
Dans ce cas, "(n j)" apparait après *Received data* dans le log (n étant le
nombre de jours). La consommation journalière correspond toujours au
dernier relevé publié.

Dans le tableau de bord Energie de Home Assistant, la consommation de gaz
au jour le jour aura un décalage de deux jours (actuellement),
contrairement au graphique apexcharts-card, auquel nous avons pu imposer un
décalage de deux jours, afin de le caler correctement.

#### Suivre l'exécution du script

Vous pouvez suivre le résultat du fonctionnement du script en définissant
deux *Sensors* supplémentaires: pour la "journée gazière" du dernier relevé
reçu, et un autre avec le résultat de la dernière exécution du script.

```yaml
homeassistant:
# autoriser l'utilisation d'un File sensor dans ce dossier
  allowlist_external_dirs:
    - "/config/gazpar/"

sensor:
  - platform: file
    name: "GRDF Log"
    file_path: ./gazpar/activity.log
    # enlever la date en début de ligne
    value_template: "{{ value[10:] }}"

templates:
  - sensor:
      name: "GRDF journée gazière"
      device_class: "timestamp"
      # compléter la date avec heure et fuseau horaire
      # prendre 18h pour un affichage plus fidèle du temps écoulé en fin de journéee
      state: "{{ state_attr('sensor.grdf_consommation_gaz', 'date') + 'T18:00:00+01:00' }}"
```

#### Messages dans *activity.log*

Voici un aperçu des messages que vous risquez de rencontrer dans le log.

- `Received data`: au moins un nouveau relevé a été reçu. Comme information
  supplémentaire, on peut y trouver:
  
  - `(n j.)`: plusieurs relevés ont été publiées depuis la dernière lecture
    (n indique leur nombre), dont le script a extrait l'évolution de
    *index_m3* et *index_kWh*. La consommation correspond à la consommation
    publiée dans le relevé le plus récent.
  - `(absDonn)`: parmi les relevés reçus, au moins un portait la notion
    "Absence de données", et ne comportait aucune information de
    consommation. Dans ce cas, l'*index_kWh* ne peut pas être calculé comme
    d'habitude (cumul des valeurs de *energieConsomme*). Il est alors
    calculé en fonction de l'évolution de l'*index_m3* et du coefficient de
    conversion.
  - `(miss)`: le script détecte une longue période d'inactivité (plus que
    sept jours). Dans ce cas, il se comporte comme dans le cas précédent
    (*absDonn*).

- `Absence de données`: Le dernier des relevés reçus ne contient aucune
  donnée de consommation. Dans ce cas, le script attend des temps
  meilleurs, notamment un relevé contenant des données de consommation.

- `No new data`: La connexion à l'espace client s'est déroulé correctement,
  mais... rien de nouveau.

- `Aucun relevé reçu`: La connexion à l'espace client a été possible, mais
  la liste des relevés était vide.

- `[No data received], [Error Invalid data]`: Le script n'a pas pu
  interpréter la réponse reçue pendant la connexion. Il ne s'agissait
  probablement pas d'une liste de relevés. Dans ce cas, il tente
  d'enregistrer la réponse en question dans le fichier `invalid_data.txt`.
  D'autres erreurs qui surviennent lors d'une tentative de connexion sont
  également signalées de cette manière.

- `Script version..., Reset daily conso`: messages écrites par l'Automation
  *GRDF Reset*.

#### Une autre façon d'enregistrer les paramètres de connexion à l'espace client GRDF

Si le fait de retrouver ces paramètres dans les *input\_\_text* ne vous
plait pas, vous pouvez procéder de la façon suivante (proposée par
olivier6931): dans secrets.yaml, remplacez les trois lignes concernant les
paramètres de connexion par celle-ci :

```yaml
grdf_get_data: '/config/gazpar/gazpar_ha.sh fetch {{ "votre@adresse.email" | base64_encode }} {{ "password" | base64_encode }} votre_pce'
```

Puis, dans `configuration.yaml` faites référence à cette ligne :

```yaml
shell_command:
    grdf_get_data: !secret grdf_get_data
```

Vous pouvez supprimer les trois *input_text* dans `configuration.yaml`.

\--

Un grand merci à [Emmanuel](https://github.com/empierre),
[Fabien](https://github.com/beufanet),
[Cyprien](https://github.com/cyprieng) et
[Yukulehe](https://github.com/yukulehe) pour l'élaboration du script
d'accès à l'espace client GRDF.
