FROM python:3.8.1-alpine3.10

LABEL "com.github.actions.name"="Generate Readme from data"
LABEL "com.github.actions.description"="Automatically generate readme from the json data files"
LABEL "com.github.actions.icon"="corner-up-left"
LABEL "com.github.actions.color"="red"

LABEL "repository"="https://github.com/ariasmartinez/dds-rtps"
LABEL "homepage"=""
LABEL "maintainer"="Celia <ariasmartinez@correo.ugr.es>"

ADD  ./src/generate_names.sh / generate_names.sh
ENTRYPOINT ["sh", "/generate_names.sh"]

