#!/bin/bash
set -e

export IP=$(hostname -I | cut -d ' ' -f 1 | xargs)


curl --location --request POST "http://${IP}:9001/services" \
--form 'port="3000"' \
--form 'name="lance"' \
--form 'host="lance"'

curl --location --request POST "http://${IP}:9001/services/lance/routes" \
--form 'paths[]="/"' \
--form 'strip_path="false"'

curl --location --request POST "http://${IP}:9001/services" \
--form 'port="8000"' \
--form 'name="coreliaos"' \
--form 'host="coreliaos"'

curl --location --request POST "http://${IP}:9001/services/coreliaos/routes" \
--form 'paths[]="/api"' \
--form 'strip_path="false"'
