#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import logging
import time
import argparse
import datetime

from threading import Thread

from Interfaces.Config import Config
from Interfaces.Geolocation import Geolocation
from Interfaces.Scanner import Scanner as tScanner
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import Scanner as dbScanner
from Interfaces.MySQL.Schema import ScannerServer as dbScannerServer


#from pogom.search import search_loop
#from pogom.pgoapi.utilities import get_pos_by_name

log = logging.getLogger(__name__)


def _arg_parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--server', type=int, help='Индекс сервера', default=1)

    args = parser.parse_args()

    return args


def _thread_start(scanner):
    log.info("Инициализируем сканнер id={0}".format(scanner.id))

    scanner_thread = tScanner(scanner.id)

    return scanner_thread

def _thread_check(thread):
    scanner_id = int(thread.name)
    scanner = session_mysql.query(dbScanner).get(scanner_id)

    if scanner.statistic.date_start + datetime.timedelta(minutes=5) < datetime.datetime.now():
        log.info("[{0} - Найден битый сканнер".format(scanner.id))

        thread.join()
        thread = _thread_start(scanner)

    return thread

arguments = _arg_parse()
config = Config()

session_maker = init(config)
session_mysql = session_maker()

scanner_alive = True

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(module)11s] [%(levelname)7s] %(message)s')

    logging.getLogger("peewee").setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("pogom.pgoapi.pgoapi").setLevel(logging.WARNING)
    logging.getLogger("pogom.pgoapi.rpc_api").setLevel(logging.INFO)


    threads = []

    server = session_mysql.query(dbScannerServer).get(arguments.server)

    if not server:
        log.error('Сервер с таким идентификатором не найден.')
        sys.exit()

    for scanner in server.scanners:
        if scanner.is_enable:
            threads.append(_thread_start(scanner))
        else:
            log.info("Cканнер id={0}, отключен, пропускаем".format(scanner.id))

    session_mysql.close()

    log.info("Запускаем потоки с интервалом в 10 сек")
    for thread in threads:
        thread.start()

        time.sleep(10)

    time.sleep(60)
    log.info("Проверяем состояния тредов.")
    while scanner_alive == True:
        for thread in threads:
            thread = _thread_check(thread)

        time.sleep(10)

    log.info("Отработали, закрываемся")

