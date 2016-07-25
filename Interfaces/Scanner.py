#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import struct
import logging
import requests
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
        self._sleepperiod = 1

        self.api = PGoApi()

        self.daemon = True


    def _statistic_clean(self):
        self.scanner.statistic.date_start = datetime.datetime.now()
        self.scanner.statistic.pokemons = 0
        self.scanner.statistic.pokestops = 0
        self.scanner.statistic.gyms = 0

        self.session_mysql.commit()
        self.session_mysql.flush()

    def _statistic_apply(self, report):
        try:
            self.scanner.statistic.pokemons += report['pokemons']
            self.scanner.statistic.pokestops += report['pokestops']
            self.scanner.statistic.gyms += report['gyms']

            self.session_mysql.commit()
            self.session_mysql.flush()
        except:
            log.error('Error save stats.')


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
        log.info('[{0}] - Attempting login.'.format(self.scanner.id))

        self.api.set_position(*self.scanner.location.position)

        while not self.api.login(self.scanner.account.service, self.scanner.account.username, self.scanner.account.password):
            log.info('[{0}] - Login failed. Trying again. [{1},{2}]'.format(self.scanner.id, self.scanner.account.username, self.scanner.account.password))
            self._stopevent.wait(self._sleepperiod)

        log.info('[{0}] - Login successful.'.format(self.scanner.id))


    def run(self):
        self.scanner.location.fix(self.geolocation)

        while not self._stopevent.isSet():
            self.run_scanner()
            self._stopevent.wait(self._sleepperiod)

        log.info("[{0}] - Отключаем сканнер".format(self.scanner.id))
        self.stop()

    def stop(self):
        self.session_mysql.close()

    def run_scanner(self):
        """ main control loop """
        log.info("[{0}] - Запускаем сканнер".format(self.scanner.id))

        self._statistic_clean()

        if self.api._auth_provider and self.api._auth_provider._ticket_expire:
            remaining_time = self.api._auth_provider._ticket_expire/1000 - time.time()

            if remaining_time > 60:
                log.info("[{0}] - Skipping login process since already logged in for another {1} seconds".format(self.scanner.id,remaining_time))
            else:
                self.login()
        else:
            self.login()

        i = 1
        for step_location in self.generate_location_steps(self.scanner.location.position, self.scanner.location.steps):
            if not self._stopevent.isSet():
                log.info('[{:d}] - Scanning step {:d} of {:d}.'.format(self.scanner.id, i, self.scanner.location.steps**2))
                log.debug('[{:d}] - Scan location is {:f}, {:f}'.format(self.scanner.id, step_location[0], step_location[1]))

                response_dict = self.send_map_request(step_location)
                while not response_dict and not self._stopevent.isSet():
                    log.info('[{:d}] - Map Download failed. Trying again.'.format(self.scanner.id))
                    response_dict = self.send_map_request(step_location)
                    self._stopevent.wait(self._sleepperiod)

                try:
                    self._statistic_apply(parse_map(response_dict, self.session_mysql))
                except KeyError:
                    log.error('[{:d}] - Scan step failed. Response dictionary key error.'.format(self.scanner.id))

                log.info('[{:d}] - Completed {:5.2f}% of scan.'.format(self.scanner.id, (float(i) / 10**2)*100))
                i += 1


    def join(self, timeout=None):
        """ Stop the thread and wait for it to end. """
        self._stopevent.set()
        threading.Thread.join(self, timeout)
        self.stop()


