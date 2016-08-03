# -*- coding: utf-8 -*-

import os
import json
import time
import pprint

import logging

from math import ceil
from s2sphere import CellId, LatLng
from google.protobuf.internal import encoder

from Interfaces import analyticts_timer
from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Stepper import get_cell_ids
from Interfaces.AI.Worker.Utils import distance, i2f, format_time
from Interfaces.MySQL.Schema import parse_map_cell

from Interfaces.pgoapi.utilities import f2i, h2f


log = logging.getLogger(__name__)


class Normal(object):
    def __init__(self, ai):
        self.ai = ai
        self.thread = ai.thread
        self.api = ai.api
        self.config = ai.thread.config
        self.scanner = ai.scanner
        self.profile = ai.profile
        self.inventory = ai.inventory
        self.metrica = ai.metrica
        self.session = ai.session
        self.search = ai.search
        self.geolocation = ai.geolocation

        self.walk = self.scanner.mode.walk
        self.step = self.scanner.mode.step
        self.distance = self.scanner.location.distance * 1000

        self.origin_lat = ai.position[0]
        self.origin_lon = ai.position[1]

        self.google_path = ""

    def take_step(self):
        position = [self.origin_lat, self.origin_lon, 0]
        coords = self.generate_coords(self.origin_lat, self.origin_lon, self.step, self.distance)

        self.metrica.take_position(position, self.geolocation.get_google_polilyne(coords))
        self.api.set_position(*position)

        step = 1
        for coord in coords:
            # starting at 0 index
            self.metrica.take_status(scanner_msg='Квадратичное сканирование ({} / {})'.format(step, len(coords)))
            log.info('Квадратичное сканирование ({} / {})'.format(step, len(coords)))

            position = (coord['lat'], coord['lng'], 0)

            if self.walk > 0:
                self._walk_to(self.walk, *position)
            else:
                self.api.set_position(*position)
            sleep(1)
            self._work_at_position(position[0], position[1], position[2], seen_pokemon=True, seen_pokestop=True, seen_gym=True)

            sleep(10)
            step += 1

    def _walk_to(self, speed, lat, lng, alt):
        dist = distance(i2f(self.api._position_lat), i2f(self.api._position_lng), lat, lng)
        steps = (dist + 0.0) / (speed + 0.0)  # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps

        log.info('Бежим из ' + str((i2f(self.api._position_lat), i2f(self.api._position_lng))) + " в " + str(str((lat, lng))) +
                   " по прямой. " + str(format_time(ceil(steps))))

        if steps != 0:
            dLat = (lat - i2f(self.api._position_lat)) / steps
            dLng = (lng - i2f(self.api._position_lng)) / steps

            for i in range(intSteps):
                cLat = i2f(self.api._position_lat) + dLat + random_lat_long_delta()
                cLng = i2f(self.api._position_lng) + dLng + random_lat_long_delta()
                self.api.set_position(cLat, cLng, alt)
                self.ai.heartbeat()

                self._work_at_position(i2f(self.api._position_lat), i2f(self.api._position_lng), alt, seen_pokemon=True, seen_pokestop=False, seen_gym=False)
                sleep(2)
            self.api.set_position(lat, lng, alt)
            self.ai.heartbeat()


    def _work_at_position(self, lat, lng, alt, seen_pokemon=False, seen_pokestop=False, seen_gym=False):
        position = (lat, lng, alt)
        cellid = get_cell_ids(lat, lng)
        timestamp = [0, ] * len(cellid)
        map_cells = list()

        self.api.get_map_objects(latitude=f2i(lat), longitude=f2i(lng),  since_timestamp_ms=timestamp, cell_id=cellid)

        response_dict = self.api.call()
        sleep(0.2)
        self.search.search(lat, lng)

        if response_dict and 'status_code' in response_dict:
            if response_dict['status_code'] is 1:
                if 'responses' in response_dict:
                    if 'GET_MAP_OBJECTS' in response_dict['responses']:
                        if 'status' in response_dict['responses']['GET_MAP_OBJECTS']:
                            if response_dict['responses']['GET_MAP_OBJECTS']['status'] is 1:
                                map_cells = response_dict['responses']['GET_MAP_OBJECTS']['map_cells']

                                # Update current scanner location
                                self.metrica.take_position(position)

                                map_cells.sort(key=lambda x: distance(lat, lng, x['forts'][0]['latitude'], x['forts'][0]['longitude']) if 'forts' in x and x['forts'] != [] else 1e6)

                                log.debug("Получена информация о карте в размере {0} ячеек".format(len(map_cells)))
                                for cell in map_cells:
                                    self.metrica.take_search(parse_map_cell(cell, self.session))

                            else:
                                log.warning("Получен неверный статус: {0}".format(response_dict['responses']['GET_MAP_OBJECTS']['status']))
            else:
                log.warning("Получен неверный статус: {0}".format(response_dict['status_code']))
        while not self.search.response.empty():
            cell = self.search.response.get()
            self.metrica.take_search(parse_map_cell(cell, self.session))
            self.search.response.task_done()

        self.api.set_position(lat, lng, alt)
        sleep(2)
        for cell in map_cells:
            self.ai.work_on_cell(cell, position,  seen_pokemon=seen_pokemon,  seen_pokestop=seen_pokestop, seen_gym=seen_gym)

    @staticmethod
    def generate_coords(latitude, longitude, step_size, distance_limit):
        coords = [{'lat': latitude, 'lng': longitude}]
        step_limit = distance_limit/step_size*100
        x = 0
        y = 0
        dx = 0
        dy = -1

        while True:
            if -step_limit / 2 < x <= step_limit / 2 and -step_limit / 2 < y <= step_limit / 2:
                lat = latitude + x * 0.8 * step_size + random_lat_long_delta()
                lng = longitude + y * step_size + random_lat_long_delta()

                coords.append({'lat': lat, 'lng': lng})
                if distance(latitude, longitude, lat, lng) > distance_limit:
                     break
            if x == y or x < 0 and x == -y or x > 0 and x == 1 - y:
                (dx, dy) = (-dy, dx)

            (x, y) = (x + dx, y + dy)

        return coords

