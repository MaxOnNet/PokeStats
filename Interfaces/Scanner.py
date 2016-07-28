#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import random
import threading
import time
from random import randint

from google.protobuf.internal import encoder
from s2sphere import CellId, LatLng

from Interfaces.Config import Config
from Interfaces.Geolocation import Geolocation
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import Scanner as dbScanner
from Interfaces.MySQL.Schema import parse_map, parse_fort

from Interfaces.pgoapi.utilities import f2i
from Interfaces.pgoapi import PGoApi

from AI.Profile import Profile

log = logging.getLogger(__name__)

#TIMESTAMP = '\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000'


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
        #log.info('[{0}] - {1} - {2}.'.format(self.scanner.id, active, state))

        self.scanner.is_active = active

        if state != "":
            self.scanner.state = state

        try:
            self.session_mysql.commit()
            self.session_mysql.flush()
        finally:
            pass

    def _status_account_apply(self, active=0, state=""):
        #log.info('[{0}] - {1} - {2}.'.format(self.scanner.id, active, state))

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
            self.api.set_position(position[0], position[1], 0)

            cell_ids = self.get_cell_ids(position[0], position[1])
            timestamps = [0,] * len(cell_ids)

            self.api.get_map_objects(latitude=f2i(position[0]),
                                longitude=f2i(position[1]),
                                since_timestamp_ms = timestamps,
                                cell_id=cell_ids)

            return self.api.call()

        except Exception as e:
            log.warn("Uncaught exception when downloading map "+ e)
            return False


    def generate_spiral(self, latitude, longitude, step_size, step_limit):
        coords = [{'lat': latitude, 'lng': longitude}]
        steps,x,y,d,m = 1, 0, 0, 1, 1
        rlow = 0.0
        rhigh = 0.0005

        while steps < step_limit:
            while 2 * x * d < m and steps < step_limit:
                x = x + d
                steps += 1
                lat = x * step_size + latitude + random.uniform(rlow, rhigh)
                lng = y * step_size + longitude + random.uniform(rlow, rhigh)
                coords.append({'lat': lat, 'lng': lng})
            while 2 * y * d < m and steps < step_limit:
                y = y + d
                steps += 1
                lat = x * step_size + latitude + random.uniform(rlow, rhigh)
                lng = y * step_size + longitude + random.uniform(rlow, rhigh)
                coords.append({'lat': lat, 'lng': lng})

            d = -1 * d
            m = m + 1
        return coords

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
        except Exception as e:
            self._status_scanner_apply(1, "Ошибка авторизации, выходим")
            log.error(str(e))
            return False

        #profile = Profile(self.api)

        step_size = 0.00111
        step_max = self.scanner.location.steps
        step_index = 1

        if self.scanner.location.is_fast:
            log.info("User FAST mode")
            step_size = 0.005

        for step_location in self.generate_spiral(self.scanner.location.position[0], self.scanner.location.position[1], step_size,step_max):
            step_position = (step_location['lat'], step_location['lng'])

            if not self._stopevent.isSet():
                self._status_scanner_apply(1, "Сканирование, шаг {0} из {1}.".format(step_index, step_max))

                response_count = 0
                response_count_max = 5

                response_dict = self.send_map_request(step_position)
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
                    self.fort_scanner(response_dict)
                except Exception as e:
                    self._status_scanner_apply(1, "Scan step failed. Response dictionary key error, skip step")
                    log.error(str(e))

                step_index += 1
            else:
                self._status_scanner_apply(1, "Сигнал на выход, завершаем работу")
                return False

        return True


    def fort_scanner(self, map_dict):
        cells = map_dict['responses']['GET_MAP_OBJECTS']['map_cells']
        for cell in cells:
            for f in cell.get('forts', []):
                fort_id = f['id']
                fort_type = f.get('type')
                fort_name = ""
                fort_image = ""
                fort_description = ""

                try:
                    self.api.fort_details(fort_id=f['id'],
                                  latitude=f['latitude'],
                                  longitude=f['longitude'])

                    response_dict = self.api.call()

                    parse_fort(fort_id, fort_type, response_dict, self.session_mysql)
                except Exception as e:
                    pass
                    #print e
                #try:
                #self.api.gym_state(fort_id=f['id'],
                #              latitude=f['latitude'],
                #              longitude=f['longitude'])

                #response_dict = self.api.call()
                #print response_dict
                    #parse_fort(fort_id, fort_type, response_dict, self.session_mysql)
               #except Exception as e:
               #     print e


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



    def get_cell_ids(self, lat, long, radius = 10):
        origin = CellId.from_lat_lng(LatLng.from_degrees(lat, long)).parent(15)
        walk = [origin.id()]
        right = origin.next()
        left = origin.prev()

        # Search around provided radius
        for i in range(radius):
            walk.append(right.id())
            walk.append(left.id())
            right = right.next()
            left = left.prev()

        # Return everything
        return  sorted(walk)

    def encode(self, cellid):
        output = []
        encoder._VarintEncoder()(output.append, cellid)
        return ''.join(output)