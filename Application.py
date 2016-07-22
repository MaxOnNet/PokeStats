#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging

from Interfaces.Config import Config
from threading import Thread

from pogom import config
from pogom.app import Pogom
from pogom.utils import get_args, insert_mock_data
from pogom.search import search_loop

from pogom.pgoapi.utilities import get_pos_by_name

config_xml = Config()
log = logging.getLogger(__name__)
debug=False

def start_locator_thread(config_xml):
    search_thread = Thread(target=search_loop, args=(config_xml,))
    search_thread.daemon = True
    search_thread.name = 'search_thread'
    search_thread.start()

position = get_pos_by_name(config_xml.get("map", "", "location", "Омск, 22 апреля, 14"))
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



#    if args.ignore:
#        Pokemon.IGNORE = [i.lower().strip() for i in args.ignore.split(',')]
#    elif args.only:
#        Pokemon.ONLY = [i.lower().strip() for i in args.only.split(',')]

#    if not args.mock:
#start_locator_thread(config_xml)
#    else:
#insert_mock_data("55.0506,73.3097", 6)

app = Pogom(__name__)
config['ROOT_PATH'] = app.root_path
if __name__ == '__main__':
    app.run(threaded=True, host="127.0.0.1", port="5000")