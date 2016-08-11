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

        self._level_banning = 0

    def take_throttling(self, level_throttling=0, level_error=0):
        if level_throttling == 0:
            self.scanner.is_throttled = 0
        else:
            self.scanner.is_throttled = 1

        if level_error == 0:
            self.scanner.is_warning = 0
        else:
            self.scanner.is_warning = 1

        self.session.commit()
        self.take_ping()


    def take_banning(self, level_banning=0):
        if level_banning == 0:
            self._level_banning = 0
            self.scanner.is_banned = 0
        else:
            self._level_banning += 1

            if self._level_banning > 5:
                log.warning("Суки забанили! топчемся на месте...")
                #
                # CСуки опять блокируют, 1 минуту занимаемся херней, каждые 10 сек, топчемся на 1 месте и посылаем сердцепиения
                #
                self.scanner.is_banned = 1

                for index in xrange(4):
                    self.take_ping()
                    self.thread.ai.stepper.take_step_at_position()

        self.session.commit()
        self.take_ping()


    def take_ping(self):
        self.time_await = datetime.datetime.now()
        self.scanner.statistic.date_start = datetime.datetime.now()

        if self.time_flush + datetime.timedelta(seconds=60) < datetime.datetime.now():
            log.debug("Сброс статистики в БД")
            self.time_flush = datetime.datetime.now()
            self.session.commit()
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
        is_exist_items = 0

        if 'pokemons' in response:
            self.scanner.statistic.pokemons += response['pokemons']

            if response['pokemons'] > 0:
                is_exist_items |= 1

        if 'pokestops' in response:
            self.scanner.statistic.pokestops += response['pokestops']

            if response['pokestops'] > 0:
                is_exist_items |= 1

        if 'gyms' in response:
            self.scanner.statistic.gyms += response['gyms']
            if response['gyms'] > 0:
                is_exist_items |= 1

        if is_exist_items == 0:
            self.take_banning(1)
        else:
            self.take_banning(0)

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

