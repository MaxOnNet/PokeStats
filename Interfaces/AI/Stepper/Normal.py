# -*- coding: utf-8 -*-

import os
import json
import time
import pprint

import logging

from math import ceil
from s2sphere import CellId, LatLng
from google.protobuf.internal import encoder

from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Stepper import get_cell_ids
from Interfaces.AI.Worker.Utils import distance, i2f, format_time, encode_coords

from Interfaces.pgoapi.utilities import f2i, h2f


log = logging.getLogger(__name__)


class Normal(object):
    def __init__(self, ai):
        self.ai = ai
        self.api = ai.api
        self.scanner = ai.scanner
        self.scanner_thread = ai.scanner_thread

        self.walk = self.scanner.mode.walk
        self.distance = self.scanner.location.distance * 1000

        self.origin_lat = ai.position[0]
        self.origin_lon = ai.position[1]

        self.google_path = ""

    def take_step(self):
        position = [self.origin_lat, self.origin_lon, 0]
        coords = self.generate_coords(self.origin_lat, self.origin_lon, 0.0015, self.distance)

        self.get_google_path(coords)
        self.api.set_position(*position)

        step = 1
        for coord in coords:
            # starting at 0 index
            self.scanner_thread._status_scanner_apply(1, 'Квадратичное сканирование ({} / {})'.format(step, len(coords)))

            position = (coord['lat'], coord['lng'], 0)

            if self.walk > 0:
                self._walk_to(self.walk, *position)
            else:
                self.api.set_position(*position)
            sleep(1)
            self._work_at_position(position[0], position[1], position[2])

            sleep(10*self.scanner.mode.is_human_sleep)
            step += 1

    def _walk_to(self, speed, lat, lng, alt):
        dist = distance(i2f(self.api._position_lat), i2f(self.api._position_lng), lat, lng)
        steps = (dist + 0.0) / (speed + 0.0)  # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps

        log.info('[AI] Бежим из ' + str((i2f(self.api._position_lat), i2f(self.api._position_lng))) + " в " + str(str((lat, lng))) +
                   " по прямой. " + str(format_time(ceil(steps))))

        if steps != 0:
            dLat = (lat - i2f(self.api._position_lat)) / steps
            dLng = (lng - i2f(self.api._position_lng)) / steps

            for i in range(intSteps):
                cLat = i2f(self.api._position_lat) + dLat + random_lat_long_delta()
                cLng = i2f(self.api._position_lng) + dLng + random_lat_long_delta()
                self.api.set_position(cLat, cLng, alt)
                self.ai.heartbeat()

                self._work_at_position(i2f(self.api._position_lat), i2f(self.api._position_lng), alt, False)
                sleep(2*self.scanner.mode.is_human_sleep)
            self.api.set_position(lat, lng, alt)
            self.ai.heartbeat()


    def _work_at_position(self, lat, lng, alt, pokemon_only=False):
        cellid = get_cell_ids(lat, lng)
        timestamp = [0, ] * len(cellid)

        self.api.get_map_objects(latitude=f2i(lat), longitude=f2i(lng),  since_timestamp_ms=timestamp, cell_id=cellid)

        response_dict = self.api.call()

        if response_dict and 'responses' in response_dict:
            if 'GET_MAP_OBJECTS' in response_dict['responses']:
                if 'status' in response_dict['responses']['GET_MAP_OBJECTS']:
                    if response_dict['responses']['GET_MAP_OBJECTS'][
                            'status'] is 1:
                        map_cells = response_dict['responses'][
                            'GET_MAP_OBJECTS']['map_cells']
                        position = (lat, lng, alt)

                        # Update current scanner location
                        self.scanner_thread._position_scanner_apply(position, self.google_path)

                        map_cells.sort(key=lambda x: distance(lat, lng, x['forts'][0]['latitude'], x['forts'][0]['longitude']) if 'forts' in x and x['forts'] != [] else 1e6)

                        for cell in map_cells:
                            self.ai.work_on_cell(cell, position)

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

    def get_google_path(self, coords):
        self.google_path = 'http://maps.googleapis.com/maps/api/staticmap?size=400x400&path=enc:{0}'.format(encode_coords(coords))

