#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging

from Interfaces.Config import Config
from threading import Thread

from pogom import config
from pogom.app import Pogom

from pogom.pgoapi.utilities import get_pos_by_name

config_xml = Config()
log = logging.getLogger(__name__)
debug=False

position = get_pos_by_name(config_xml.get("map", "", "location", "Омск, Менделеева, 21"))
config['ORIGINAL_LATITUDE'] = position[0]
config['ORIGINAL_LONGITUDE'] = position[1]
config['GMAPS_KEY'] = config_xml.get("map", "google", "key", "")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(module)11s] [%(levelname)7s] %(message)s')

logging.getLogger("peewee").setLevel(logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("pogom.pgoapi.pgoapi").setLevel(logging.WARNING)
logging.getLogger("pogom.pgoapi.rpc_api").setLevel(logging.INFO)


if debug:
    logging.getLogger("requests").setLevel(logging.DEBUG)
    logging.getLogger("pgoapi").setLevel(logging.DEBUG)
    logging.getLogger("rpc_api").setLevel(logging.DEBUG)




log.info('Parsed location is: {:.4f}/{:.4f}/{:.4f} (lat/lng/alt)'.
             format(*position))


app = Pogom(__name__)
config['ROOT_PATH'] = app.root_path
if __name__ == '__main__':
    app.run(threaded=True, host="127.0.0.1", port="5000")