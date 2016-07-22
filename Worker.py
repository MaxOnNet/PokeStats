#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging

from Interfaces.Config import Config
from threading import Thread

from pogom import config
from pogom.search import search_loop
from pogom.pgoapi.utilities import get_pos_by_name


log = logging.getLogger(__name__)

#position = get_pos_by_name(config_xml.get("map", "", "location", "Омск, 22 Апреля, 30"))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(module)11s] [%(levelname)7s] %(message)s')

    logging.getLogger("peewee").setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pogom.pgoapi.pgoapi").setLevel(logging.WARNING)
    logging.getLogger("pogom.pgoapi.rpc_api").setLevel(logging.INFO)

    config = Config()
    workers = []

    for worker in config.get_dict("map","worker"):
        if worker["enable"] == "True":
            print 'search_thread_{0}'.format(worker['name'])
            worker_thread = Thread(target=search_loop, args=(worker,))
            worker_thread.daemon = True
            worker_thread.name = 'search_thread_{0}'.format(worker['name'])
            worker_thread.start()

            workers.append(worker_thread)

    for worker in workers:
        worker.join()

#    if args.ignore:
#        Pokemon.IGNORE = [i.lower().strip() for i in args.ignore.split(',')]
#    elif args.only:
#        Pokemon.ONLY = [i.lower().strip() for i in args.only.split(',')]

#    if not args.mock:
#search_thread =
#search_thread.daemon = True
#search_thread.name = 'search_thread'
#search_thread.start()
#search_thread.join()
