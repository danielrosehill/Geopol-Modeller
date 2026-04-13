#! /bin/sh
# geopol_config && \
env AZURE_OPENAI_API_KEY="$(cat /run/secrets/openai_key)" geopol_simulation \
-c /home/geopol/.config/geopol/wotr_unmasked-openai.yaml \
-l /home/geopol/logs/openai/geopol.log --runs 20 \
--simulation-name WotR-Sim --simulation-mode