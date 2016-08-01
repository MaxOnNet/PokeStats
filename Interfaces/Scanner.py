#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import random
import threading
import time
from random import randint


from Interfaces.Config import Config
from Interfaces.Geolocation import Geolocation
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import Scanner as dbScanner

from Interfaces.pgoapi import PGoApi

from Interfaces.AI import AI
from Interfaces.AI.Profile import Profile

log = logging.getLogger(__name__)


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
        self.ai = AI(self)
        self.profile = Profile(self)

        self.daemon = True

        self.await = datetime.datetime.now()

    def _statistic_update(self, report=None):
        self.await = datetime.datetime.now()

        self.scanner.statistic.date_start = datetime.datetime.now()

        if report is None:
            self.scanner.statistic.pokemons = 0
            self.scanner.statistic.pokestops = 0
            self.scanner.statistic.gyms = 0
        else:
            self.scanner.statistic.pokemons += report['pokemons']
            self.scanner.statistic.pokestops += report['pokestops']
            self.scanner.statistic.gyms += report['gyms']
        try:

            self.session_mysql.commit()
            self.session_mysql.flush()
        except:
            log.error('Error save stats.')

    def _status_scanner_apply(self, active=0, state=""):
        log.info('[{0}] - {1} - {2}.'.format(self.scanner.id, active, state))

        self.scanner.is_active = active

        if state != "":
            self.scanner.state = state

        try:
            self.session_mysql.commit()
            self.session_mysql.flush()
        finally:
            pass
    def _status_account_apply(self, active=0, state=""):
        log.info('[{0}] - {1} - {2}.'.format(self.scanner.id, active, state))

        self.scanner.account.is_active = active

        if state != "":
            self.scanner.account.state = state

        try:
            self.session_mysql.commit()
            self.session_mysql.flush()
        finally:
            pass

    def _position_scanner_apply(self, position, google_path):
        try:
            self.scanner.latitude = position[0]
            self.scanner.longitude = position[1]
            self.scanner.google_path = google_path

            self.session_mysql.commit()
            self.session_mysql.flush()
        except:
            log.error('Error save stats.')


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
        self._statistic_update()

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
        except Exception as e:
            self._status_scanner_apply(1, "Ошибка авторизации, выходим")
            log.error(str(e))
            return False

        try:
            self.profile.update_profile()
            self.profile.update_inventory()
        finally:
            self.ai.heartbeat()

        self.ai.take_step()
        self.ai.heartbeat()

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

