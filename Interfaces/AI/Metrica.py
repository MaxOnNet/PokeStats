#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging

log = logging.getLogger(__name__)


class Metrica:
    def __init__(self, thread):
        self.thread = thread
        self.session = thread.session
        self.scanner = thread.scanner

        self.time_flush = datetime.datetime.now()
        self.time_await = datetime.datetime.now()

        log.debug("Обнуляем счетсчики в БД")
        self.take_status(scanner_state=0, scanner_msg="", account_state=0, account_msg="")
        self.take_position([0, 0], "")
        self.take_step()
        self.session.flush()

    def take_ping(self):
        self.time_await = datetime.datetime.now()
        self.scanner.statistic.date_start = datetime.datetime.now()

        if self.time_flush + datetime.timedelta(seconds=10) < datetime.datetime.now():
            log.debug("Сброс статистики в БД")
            self.time_flush = datetime.datetime.now()
            self.session.flush()


    def take_step(self):
        self.scanner.statistic.pokemons = 0
        self.scanner.statistic.pokestops = 0
        self.scanner.statistic.gyms = 0

        self.session.commit()
        self.take_ping()


    def take_position(self, position, google_polyline=None):
        self.scanner.latitude = position[0]
        self.scanner.longitude = position[1]

        if google_polyline is not None:
            self.scanner.google_path = google_polyline

        self.session.commit()
        self.take_ping()


    def take_search(self, response):
        if 'pokemons' in response:
            self.scanner.statistic.pokemons += response['pokemons']

        if 'pokestops' in response:
            self.scanner.statistic.pokestops += response['pokestops']

        if 'gyms' in response:
            self.scanner.statistic.gyms += response['gyms']

        self.session.commit()
        self.take_ping()


    def take_status(self, scanner_state=-1, scanner_msg=None, account_state=-1, account_msg=None):
        if scanner_state != -1:
            self.scanner.is_active = scanner_state

        if scanner_msg is not None:
            self.scanner.state = scanner_msg

        if account_state != -1:
            self.scanner.account.is_active = account_state

        if account_msg is not None:
            self.scanner.account.state = account_msg


    def _status_account_apply(self, active=0, state=""):
        log.info(state)

