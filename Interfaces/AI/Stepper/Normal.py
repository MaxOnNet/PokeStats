# -*- coding: utf-8 -*-

import os
import json
import time
import pprint

import logging

from math import ceil, sqrt
from s2sphere import CellId, LatLng
from google.protobuf.internal import encoder

from Interfaces import analyticts_timer
from Interfaces.AI.Human import sleep, random_lat_long_delta, action_delay
from Interfaces.AI.Worker.Utils import distance, i2f, format_time
from Interfaces.MySQL.Schema import parse_map_cell

from Interfaces.pgoapi.utilities import f2i, h2f, get_cell_ids


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

        self.inicialise()

        self.walk = self.scanner.mode.walk
        self.step = self.scanner.mode.step
        self.distance = self.scanner.location.distance * 1000

        self.origin_lat = ai.position[0]
        self.origin_lon = ai.position[1]

        self.google_path = ""

        self.use_search = self.scanner.mode.is_search


    def inicialise(self):
        pass

    def take_step(self):
        position = [self.origin_lat, self.origin_lon, 0]
        coords = self.generate_coords(self.origin_lat, self.origin_lon, self.step, self.distance)

        self.metrica.take_position(position, self.geolocation.get_google_polilyne(coords))
        self.api.set_position(*position)

        step = 1
        for coord in coords:
            # starting at 0 index
            self.metrica.take_status(scanner_msg='Квадратичное ({} / {})'.format(step, len(coords)))
            log.info('Квадратичное сканирование ({} / {})'.format(step, len(coords)))

            position = (coord['lat'], coord['lng'], 0)

            if self.walk > 0:
                self._walk_to(self.walk, *position)
            else:
                self.api.set_position(*position)
                self.ai.heartbeat()

            self._work_at_position(position[0], position[1], position[2], seen_pokemon=True, seen_pokestop=True, seen_gym=True)
            action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

            step += 1

    def _walk_to(self, walk_speed, dest_lat, dest_lng, alt):
        init_lat = self.api._position_lat
        init_lng = self.api._position_lng
        walk_distance = distance(init_lat, init_lng, dest_lat, dest_lng)
        walk_distance_total = max(1, walk_distance)
        walk_steps = (walk_distance + 0.0) / (walk_speed + 0.0)

        if walk_distance < walk_speed or int(walk_steps) <= 1:
            delta_lat = 0
            delta_lng = 0
            magnitude = 0
        else:
            delta_lat = (dest_lat - init_lat) / int(walk_steps)
            delta_lng = (dest_lng - init_lng) / int(walk_steps)
            magnitude = self._pythagorean(delta_lat, delta_lng)

        log.info("Бежим из [{}, {}] в [{}, {}] на расстояние {}, со скоростью {}, ориентировочно за {}".format(init_lat, init_lng, dest_lat, dest_lng, round(walk_distance, 2), walk_speed, format_time(ceil(walk_steps))))

        if (delta_lat == 0 and delta_lng == 0) or walk_distance < walk_speed:
            self.api.set_position(dest_lat, dest_lng, 0)
            return True


        while True:
            total_delta_step = walk_distance/int(walk_steps)
            total_delta_lat = (dest_lat - self.api._position_lat)
            total_delta_lng = (dest_lng - self.api._position_lng)
            magnitude = self._pythagorean(total_delta_lat, total_delta_lng)

            if distance(init_lat, init_lng, dest_lat, dest_lng) <= total_delta_step:
                self.api.set_position(dest_lat, dest_lng, alt)
                self.ai.heartbeat()
                break

            unit_lat = total_delta_lat / magnitude
            unit_lng = total_delta_lng / magnitude

            scaled_delta_lat = unit_lat * magnitude
            scaled_delta_lng = unit_lng * magnitude

            c_lat = init_lat + scaled_delta_lat + random_lat_long_delta()
            c_lng = init_lng + scaled_delta_lng + random_lat_long_delta()

            self.api.set_position(c_lat, c_lng, 0)
            self.ai.heartbeat()

            action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

            self._work_at_position(self.api._position_lat, self.api._position_lng, alt, seen_pokemon=True, seen_pokestop=False, seen_gym=False)




    def _work_at_position(self, lat, lng, alt, seen_pokemon=False, seen_pokestop=False, seen_gym=False, data=None):
        position = (lat, lng, alt)
        map_cells = []
        sleep(self.ai.delay_scan)

        if self.use_search:
            self.search.search(lat, lng)

        try:
            response_index = 0

            while response_index < 5:
                cellid = get_cell_ids(lat, lng)
                timestamp = [1, ] * len(cellid)

                self.api.set_position(lat, lng, 0)
                response_dict = self.api.get_map_objects(latitude=f2i(lat), longitude=f2i(lng),  since_timestamp_ms=timestamp, cell_id=cellid)

                if response_dict and 'status_code' in response_dict:
                    if response_dict['status_code'] is 1:
                        if 'responses' in response_dict:
                            if 'GET_MAP_OBJECTS' in response_dict['responses']:
                                if 'status' in response_dict['responses']['GET_MAP_OBJECTS']:
                                    if response_dict['responses']['GET_MAP_OBJECTS']['status'] is 1:
                                        map_cells = response_dict['responses']['GET_MAP_OBJECTS']['map_cells']
                                        response_index = 999

                                        # Update current scanner location
                                        self.metrica.take_position(position)

                                        map_cells.sort(key=lambda x: distance(lat, lng, x['forts'][0]['latitude'], x['forts'][0]['longitude']) if 'forts' in x and x['forts'] != [] else 1e6)

                                        log.debug("Получена информация о карте в размере {0} ячеек".format(len(map_cells)))
                                        for cell in map_cells:
                                            self.metrica.take_search(parse_map_cell(cell, self.session))

                                    else:
                                        log.warning("Получен неверный статус: {0}".format(response_dict['responses']['GET_MAP_OBJECTS']['status']))
                                        action_delay(self.ai.delay_action_min, self.ai.delay_action_max)
                    else:
                        log.debug("Получен неверный статус: {0}".format(response_dict['status_code']))

                        if response_dict['status_code'] == 52:
                            response_index += 1
                            action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

        except Exception as e:
            log.error("Ошибка в обработке дочернего потока: {}".format(e))

        if self.use_search:
            log.info("Ожидаем конца сканирования, и по ходу парсим данные")
            while not self.search.requests.empty():
                if not self.search.response.empty():
                    cell = self.search.response.get()
                    self.metrica.take_search(parse_map_cell(cell, self.session))
                    self.search.response.task_done()

            while not self.search.response.empty():
                cell = self.search.response.get()
                self.metrica.take_search(parse_map_cell(cell, self.session))
                self.search.response.task_done()

        self.api.set_position(lat, lng, alt)

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


    def _pythagorean(self, lat, lng):
        return sqrt((lat ** 2) + (lng ** 2))
