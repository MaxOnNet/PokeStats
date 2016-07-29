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
from Interfaces.AI.Worker.Utils import distance, i2f, format_time

from Interfaces.pgoapi.utilities import f2i, h2f


log = logging.getLogger(__name__)


class Normal(object):
    def __init__(self, ai):
        self.ai = ai
        self.api = ai.api
        self.scanner = ai.scanner
        self.scanner_thread = ai.scanner_thread
        self.pos = 1
        self.x = 0
        self.y = 0
        self.dx = 0
        self.dy = -1

        self.steplimit = self.scanner.location.steps
        self.steplimit2 = self.scanner.location.steps**2

        self.origin_lat = self.scanner.location.latitude
        self.origin_lon = self.scanner.location.longitude

    def take_step(self):
        position = (self.scanner.location.latitude, self.scanner.location.longitude, 0.0)

        self.api.set_position(*position)
        for step in range(self.steplimit2):
            # starting at 0 index
            self.scanner_thread._status_scanner_apply(1, '[AI] Scanning area for objects ({} / {})'.format((step + 1), self.steplimit**2))

            log.debug('steplimit: {} x: {} y: {} pos: {} dx: {} dy {}'.format(
                        self.steplimit2, self.x, self.y, self.pos, self.dx,self.dy))

            # Scan location math
            if -self.steplimit2 / 2 < self.x <= self.steplimit2 / 2 and -self.steplimit2 / 2 < self.y <= self.steplimit2 / 2:
                position = (self.x * 0.0025 + self.origin_lat,
                            self.y * 0.0025 + self.origin_lon, 0)
                if self.scanner.location.walk > 0:
                    self._walk_to(self.scanner.location.walk, *position)
                else:
                    self.api.set_position(*position)
            if self.x == self.y or self.x < 0 and self.x == -self.y or self.x > 0 and self.x == 1 - self.y:
                (self.dx, self.dy) = (-self.dy, self.dx)

            (self.x, self.y) = (self.x + self.dx, self.y + self.dy)

            self._work_at_position(position[0], position[1], position[2], True)
            sleep(1)

    def _walk_to(self, speed, lat, lng, alt):
        dist = distance(i2f(self.api._position_lat), i2f(self.api._position_lng), lat, lng)
        steps = (dist + 0.0) / (speed + 0.0)  # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps

        self.scanner_thread._status_scanner_apply(1, '[AI] Walking from ' + str((i2f(self.api._position_lat), i2f(self.api._position_lng))) + " to " + str(str((lat, lng))) +
                   " for approx. " + str(format_time(ceil(steps))))

        if steps != 0:
            dLat = (lat - i2f(self.api._position_lat)) / steps
            dLng = (lng - i2f(self.api._position_lng)) / steps

            for i in range(intSteps):
                cLat = i2f(self.api._position_lat) + dLat + random_lat_long_delta()
                cLng = i2f(self.api._position_lng) + dLng + random_lat_long_delta()
                self.api.set_position(cLat, cLng, alt)
                self.ai.heartbeat()

                self._work_at_position(i2f(self.api._position_lat), i2f(self.api._position_lng), alt, False)
                sleep(1)
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
                        self.scanner_thread._position_scanner_apply(position)

                        map_cells.sort(key=lambda x: distance(lat, lng, x['forts'][0]['latitude'], x['forts'][0]['longitude']) if 'forts' in x and x['forts'] != [] else 1e6)

                        for cell in map_cells:
                            self.ai.work_on_cell(cell, position, pokemon_only)
