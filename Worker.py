#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import logging
import time
import argparse

from threading import Thread


from Interfaces.Config import Config
from Interfaces.Geolocation import Geolocation
from Interfaces.Scanner import search_loop
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import Scanner, ScannerServer, ScannerAccount, ScannerLocation


#from pogom.search import search_loop
#from pogom.pgoapi.utilities import get_pos_by_name


log = logging.getLogger(__name__)

def _arg_parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--server', type=int, help='Индекс сервера', default=1)

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(module)11s] [%(levelname)7s] %(message)s')

    logging.getLogger("peewee").setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pogom.pgoapi.pgoapi").setLevel(logging.WARNING)
    logging.getLogger("pogom.pgoapi.rpc_api").setLevel(logging.INFO)

    arguments = _arg_parse()
    config = Config()

    session_maker = init(config)
    session_mysql = session_maker()

    threads = []

    server = session_mysql.query(ScannerServer).get(arguments.server)

    if not server:
        log.error('Сервер с таким идентификатором не найден.')
        sys.exit()

    for scanner in server.scanners:
        if scanner.is_enable:
            log.info("Инициализируем сканнер id={0}".format(scanner.id))

            scanner_thread = Thread(target=search_loop, args=(int(scanner.id),))
            scanner_thread.daemon = True
            scanner_thread.name = 'scanner_thread_{0}'.format(scanner.id)

            threads.append(scanner_thread)
        else:
            log.info("Cканнер id={0}, отключен, пропускаем".format(scanner.id))

    session_mysql.close()

    log.info("Запускаем потоки с интервалом в 10 сек")
    for thread in threads:
        thread.start()

        time.sleep(10)

    log.info("Подключаемся к потокам и ждем конца")
    for thread in threads:
        thread.join()


    log.info("Отработали, закрываемся")

