#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import logging
import time
import argparse
import datetime
import threading

from Interfaces.Config import Config
from Interfaces.Scanner import Scanner as tScanner
from Interfaces.MySQL import init_fast as init
from Interfaces.MySQL.Schema import Scanner as dbScanner
from Interfaces.MySQL.Schema import ScannerServer as dbScannerServer

log = logging.getLogger(__name__)


def _arg_parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--server', type=int, help='Индекс сервера', default=1)

    args = parser.parse_args()

    return args


def _touch_pid(worker_id=1):
    worker_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
    worker_pid = str(os.getpid())
    worker_pidfile = "{0}/.run/worker.{1}.pid".format(worker_path, worker_id)

    file(worker_pidfile, 'w').write(worker_pid)


def _touch_log(worker_id=1):
    worker_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
    logging.basicConfig(filename="{0}/.log/worker.{1}.log".format(worker_path, worker_id), filemode='w', level=logging.INFO, format='%(asctime)s [%(module)15s] [%(funcName)15s] [%(lineno)4d] [%(levelname)7s] [%(threadName)5s] %(message)s')

    logging.getLogger("peewee").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("Interfaces.pgoapi.pgoapi").setLevel(logging.WARNING)
    logging.getLogger("Interfaces.pgoapi.rpc_api").setLevel(logging.WARNING)
    logging.getLogger("Interfaces.AI.Metrica").setLevel(logging.DEBUG)


def _thread_start(scanner):
    log.info("Инициализируем сканнер id={0}".format(scanner.id))

    scanner_thread = tScanner(scanner.id)
    scanner_thread.start()

    time.sleep(10)

    return scanner_thread


def _thread_check(thread):

    scanner_id = int(thread.name)
    scanner = session_mysql.query(dbScanner).get(scanner_id)


# Проверка на только включенные при рабочем сервере
    if thread.metrica.time_await + datetime.timedelta(minutes=15) < datetime.datetime.now():
        log.info("[{0} - Найден битый сканнер".format(scanner.id))

        thread.join()


arguments = _arg_parse()
config = Config()

session_maker = init(config)
session_mysql = session_maker()

scanner_alive = True
if __name__ == '__main__':
    threading.current_thread().name = '00-00'

    threads = []

    server = session_mysql.query(dbScannerServer).get(arguments.server)

    if not server:
        log.error('Сервер с таким идентификатором не найден.')
        sys.exit()

    for scanner in server.scanners:
        log.info('Обнуление статистики для сканера:{0}.'.format(scanner.id))
        scanner.state = ""
        scanner.is_active = 0
        scanner.is_throttled = 0
        scanner.is_warning = 0
        scanner.is_banned = 0

        scanner.statistic.date_start = datetime.datetime.now()
        scanner.statistic.pokemons = 0
        scanner.statistic.pokestops = 0
        scanner.statistic.gyms = 0
        scanner.account.state = ""
        scanner.account.is_active = 0

        if not server.is_enable:
            scanner.state = "Сервер выключен"
    session_mysql.commit()
    session_mysql.flush()

    if server.is_enable:
        for scanner in server.scanners:
            if scanner.is_enable == 1:
                threads.append(_thread_start(scanner))
            else:
                scanner.is_active = 0
                scanner.state = "Отключен, пропуск"

                try:
                    session_mysql.commit()
                    session_mysql.flush()
                finally:
                    pass
                log.info("Cканнер id={0}, отключен, пропускаем".format(scanner.id))


        time.sleep(60)
        log.info("Проверяем состояния тредов.")

        while scanner_alive == True:
            session_mysql.commit()
            session_mysql.flush()
            session_mysql.expunge_all()

            log.info("Начинаем проверку, в пуле {0} потоков".format(len(threads)))

            for thread in threads:
                if thread.is_alive() and thread.alive:
                    _thread_check(thread)
                else:
                    log.info("Тред мертв, удаляем из пула")
                    threads.remove(thread)

            server = session_mysql.query(dbScannerServer).get(arguments.server)
            log.info("После сканирования осталось {0} потоков".format(len(threads)))
            for scanner in server.scanners:
                scanner_exist = False
                scanner_thread = None

                for thread in threads:
                    if str(thread.name) == str(scanner.id):
                        scanner_exist = True

                if scanner.is_enable:
                    if not scanner_exist:
                        log.warning("Сканнер {0} не найден, запускаем".format(scanner.id))
                        threads.append(_thread_start(scanner))
                else:
                    if scanner_exist and scanner_thread is not None:
                        log.warning("Cканнер id={0}, отключен, завершаем его работу".format(scanner.id))
                        scanner_thread.join()

            time.sleep(10)

    session_mysql.close()
    log.info("Отработали, закрываемся")


