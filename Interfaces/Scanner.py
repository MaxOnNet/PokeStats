#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import random
import threading
import time
from random import randint

from Interfaces import analyticts_timer
from Interfaces.Config import Config
from Interfaces.Geolocation import Geolocation
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import Scanner as dbScanner

from Interfaces.pgoapi import PGoApi

from Interfaces.AI import AI
from Interfaces.AI.Profile import Profile
from Interfaces.AI.Inventory import Inventory
from Interfaces.AI.Metrica import Metrica

log = logging.getLogger(__name__)


class Scanner(threading.Thread):
    def __init__(self, scanner_id):
        threading.Thread.__init__(self, name=scanner_id)

        self.config = Config()
        self.geolocation = Geolocation(self)
        self.session_maker = init(self.config)
        self.session = self.session_maker()

        self.scanner = self.session.query(dbScanner).get(scanner_id)

        self._stopevent = threading.Event()

        self._sleepperiod = 10
        self._sleeplogin = 20

        self.api = PGoApi()
        self.api.activate_signature(self.config.get("AI", "", "signature", "tess"))


        self.profile = Profile(self)
        self.inventory = Inventory(self)
        self.metrica = Metrica(self)

        self.ai = AI(self)

        self.daemon = True

    def login(self):
        login_count = 0
        login_count_max = 5

        self.metrica.take_status(account_state=1, account_msg="Попытка авторизации ({0})".format(login_count))
        log.debug("Попытка авторизации ({0})".format(login_count))

        self.api.set_position(self.scanner.location.latitude, self.scanner.location.longitude, 0)

        while not self.api.login(self.scanner.account.service, self.scanner.account.username, self.scanner.account.password):
            if login_count < login_count_max:
                self.metrica.take_status(account_state=1, account_msg="Ошибка авторизации ({0}), ожидаем".format(login_count))
                log.warning("Ошибка авторизации ({0}), ожидаем".format(login_count))

                self._stopevent.wait(randint(self._sleeplogin, self._sleeplogin*3))

                login_count += 1
            else:
                self.metrica.take_status(account_state=0, account_msg="Успешная авторизация")
                log.warning("Ошибка авторизации, выходим")

                return False

        self.metrica.take_status(account_state=1, account_msg="Успешная авторизация")
        log.info("Успешная авторизация")

        return True


    def run(self):
        self.alive = True
        self.scanner.location.fix(self.geolocation)

        self.metrica.take_status(scanner_state=1, scanner_msg="Запускаем сканнер", account_state=1)
        log.info("Запускаем сканнер")

        while not self._stopevent.isSet():
            if not self.run_scanner():
                self._stopevent.set()
                break
            else:
                self.metrica.take_status(scanner_state=1, scanner_msg="Ожидаем следующего цикла")

                log.info("Ожидаем следующего цикла")

                self._stopevent.wait(randint(self._sleepperiod, self._sleepperiod*2))
        try:
            self.metrica.take_status(scanner_state=0, scanner_msg="Сканнер отключен")

            self.session.commit()
            self.session.flush()
        finally:
            self.session.close()
            self.alive = False


    def run_scanner(self):
        try:
            if self.api._auth_provider and self.api._auth_provider._ticket_expire:
                remaining_time = self.api._auth_provider._ticket_expire/1000 - time.time()

                if remaining_time > 60:
                    self.metrica.take_status(scanner_state=1, scanner_msg="Уже залогинены, прускаем")
                    log.debug("Уже залогинены, прускаем")
                else:
                    if not self.login():
                        self.metrica.take_status(scanner_state=1, scanner_msg="Ошибка авторизации, выходим")
                        log.warning("Ошибка авторизации, выходим")
                        return False
            else:
                if not self.login():
                    self.metrica.take_status(scanner_state=1, scanner_msg="Ошибка авторизации, выходим")
                    log.warning("Ошибка авторизации, выходим")
                    return False
        except Exception as e:
            self.metrica.take_status(scanner_state=1, scanner_msg="Ошибка авторизации, выходим")
            log.error("Ошибка авторизации, выходим")
            log.error(str(e))

            return False

        try:
            log.info("Обновляем данные о профиле и сумке")
            self.profile.update()
            self.inventory.update()
            #self.ai.heartbeat()
        finally:
            self.session.flush()

        log.info("Начинаем обработку")
        self.ai.take_step()
        #self.ai.heartbeat()

        return True


    def join(self, timeout=None):
        log.info("Был получен сигнал заверщения работы")
        self.metrica.take_status(scanner_state=1, scanner_msg="Был получен сигнал заверщения работы")

        self._stopevent.set()
        self.ai.search.stop()

        threading.Thread.join(self, timeout)

        try:
            self.metrica.take_status(scanner_state=0, scanner_msg="Сканнер отключен")
            self.session.commit()
            self.session.flush()
        finally:
            self.session.close()
            log.info("Поток завершил работу")
