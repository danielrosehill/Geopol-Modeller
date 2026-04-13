#! /bin/sh
geopol_config && \
geopol_simulation -c /home/geopol/.config/geopol/wotr_unmasked.yaml \
-l /home/geopol/logs/local/geopol.log --runs 5 \
--simulation-name WotR-Sim --simulation-mode