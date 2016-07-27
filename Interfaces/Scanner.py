#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import struct
import logging
import requests
from random import randint
import time
import datetime
import threading
import thread

from pogom.pgoapi import PGoApi
from pogom.pgoapi.utilities import f2i, h2f, get_cellid, encode, get_pos_by_name

from Interfaces.Config import Config
from Interfaces.Geolocation import Geolocation
from Interfaces.MySQL import init

from Interfaces.MySQL.Schema import Scanner as dbScanner
from Interfaces.MySQL.Schema import parse_map


log = logging.getLogger(__name__)

TIMESTAMP = '\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000'


class Scanner(threading.Thread):
    def __init__(self, scanner_id):
        threading.Thread.__init__(self, name=scanner_id)

        self.config = Config()
        self.geolocation = Geolocation(self.config)
        self.session_maker = init(self.config)
        self.session_mysql = self.session_maker()

        self.scanner = self.session_mysql.query(dbScanner).get(scanner_id)

        self._stopevent = threading.Event()

        self._sleepperiod = 10
        self._sleeplogin = 20

        self.api = PGoApi()

        self.daemon = True
        self.alive = False
        self.await = datetime.datetime.now()

    def _statistic_clean(self):
        self.scanner.statistic.date_start = datetime.datetime.now()
        self.scanner.statistic.pokemons = 0
        self.scanner.statistic.pokestops = 0
        self.scanner.statistic.gyms = 0

        self.session_mysql.commit()
        self.session_mysql.flush()

    def _statistic_apply(self, report):
        try:
            self.await = datetime.datetime.now()
            self.scanner.statistic.date_start = datetime.datetime.now()
            self.scanner.statistic.pokemons += report['pokemons']
            self.scanner.statistic.pokestops += report['pokestops']
            self.scanner.statistic.gyms += report['gyms']

            self.session_mysql.commit()
            self.session_mysql.flush()
        except:
            log.error('Error save stats.')

    def _status_scanner_apply(self, active=0, state=""):
    #    log.info('[{0}] - {1} - {2}.'.format(self.scanner.id, active, state))

        self.scanner.is_active = active

        if state != "":
            self.scanner.state = state

        try:
            self.session_mysql.commit()
            self.session_mysql.flush()
        finally:
            pass

    def _status_account_apply(self, active=0, state=""):
      #  log.info('[{0}] - {1} - {2}.'.format(self.scanner.id, active, state))

        self.scanner.account.is_active = active

        if state != "":
            self.scanner.account.state = state

        try:
            self.session_mysql.commit()
            self.session_mysql.flush()
        finally:
            pass

    def send_map_request(self, position):
        try:
            self.api.set_position(*position)
            self.api.get_map_objects(latitude=f2i(position[0]),
                                longitude=f2i(position[1]),
                                since_timestamp_ms=TIMESTAMP,
                                cell_id=get_cellid(position[0], position[1]))
            return self.api.call()
        except Exception as e:
            log.warn("Uncaught exception when downloading map "+ e)
            return False


    def generate_location_steps(self, initial_location, num_steps):
        pos, x, y, dx, dy = 1, 0, 0, 0, -1

        while -num_steps / 2 < x <= num_steps / 2 and -num_steps / 2 < y <= num_steps / 2:
            yield (x * 0.0025 + initial_location[0], y * 0.0025 + initial_location[1], 0)

            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
                dx, dy = -dy, dx

            x, y = x + dx, y + dy


    def login(self):
        login_count = 0
        login_count_max = 5

        self._status_account_apply(1, "Попытка авторизации ({0})".format(login_count))

        self.api.set_position(*self.scanner.location.position)

        while not self.api.login(self.scanner.account.service, self.scanner.account.username, self.scanner.account.password):
            if login_count < login_count_max:
                self._status_account_apply(1, "Ошибка авторизации ({0}), ожидаем".format(login_count))

                self._stopevent.wait(randint(self._sleeplogin, self._sleeplogin*3))

                login_count += 1
            else:
                self._status_account_apply(0, "Ошибка авторизации, выходим")

                return False

        self._status_account_apply(1, "Успешная авторизация")
        return True

    def run(self):
        self.alive = True
        self.scanner.location.fix(self.geolocation)

        self._status_account_apply(1, "Запускаем сканнер")
        self._status_scanner_apply(1, "Запускаем сканнер")

        while not self._stopevent.isSet():
            if not self.run_scanner():
                self._stopevent.set()
                break
            else:
                self._status_scanner_apply(1, "Ожидаем следующего цикла")
                self._stopevent.wait(randint(self._sleepperiod, self._sleepperiod*2))
        try:
            self._status_scanner_apply(0, "Сканнер отключен")

            self.session_mysql.commit()
            self.session_mysql.flush()
        finally:
            self.session_mysql.close()
            self.alive = False

    def run_scanner(self):
        self._statistic_clean()

        try:
            if self.api._auth_provider and self.api._auth_provider._ticket_expire:
                remaining_time = self.api._auth_provider._ticket_expire/1000 - time.time()

                if remaining_time > 60:
                    self._status_scanner_apply(1, "Уже залогинены, прускаем")
                else:
                    if not self.login():
                        self._status_scanner_apply(1, "Ошибка авторизации, выходим")

                        return False
            else:
                if not self.login():
                    self._status_scanner_apply(1, "Ошибка авторизации, выходим")

                    return False
        except:
            self._status_scanner_apply(1, "Ошибка авторизации, выходим")
            return False

        i = 1
        for step_location in self.generate_location_steps(self.scanner.location.position, self.scanner.location.steps):
            if not self._stopevent.isSet():
                self._status_scanner_apply(1, "Сканирование, шаг {0} из {1}.".format(i, self.scanner.location.steps**2))

                response_count = 0
                response_count_max = 5

                response_dict = self.send_map_request(step_location)
                while not response_dict and not self._stopevent.isSet():
                    if response_count < response_count_max:
                        self._status_scanner_apply(1, "Загрузка карты не удалась ({0}), ожидаем.".format(response_count))

                        self._stopevent.wait(self._sleepperiod)
                        response_dict = self.send_map_request(step_location)

                        response_count += 1
                    else:
                        self._status_scanner_apply(1, "Загрузка карты не удалась, завершаем.")
                        return False

                try:
                    self._statistic_apply(parse_map(response_dict, self.session_mysql))
                except KeyError:
                    self._status_scanner_apply(1, "Scan step failed. Response dictionary key error, skip step")

                i += 1
                self._stopevent.wait(0.1)
            else:
                self._status_scanner_apply(1, "Сигнал на выход, завершаем работу")
                return False

        return True


    def join(self, timeout=None):
        """ Stop the thread and wait for it to end. """
        self._stopevent.set()

        threading.Thread.join(self, timeout)

        try:
            self._status_scanner_apply(1, "Был получен сигнал на выход")
            self.session_mysql.commit()
            self.session_mysql.flush()
        finally:
            self.session_mysql.close()

