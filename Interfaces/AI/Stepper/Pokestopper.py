# -*- coding: utf-8 -*-
import logging
import random
from math import ceil
from sqlalchemy import text as sql_text
from Interfaces.MySQL.Schema import Pokestop, parse_map_cell
from Interfaces.AI.Human import sleep, random_lat_long_delta, action_delay
from Interfaces.AI.Stepper.Normal import Normal
from Interfaces.AI.Worker.Utils import format_time, distance
from Interfaces.pgoapi.utilities import f2i, h2f, get_cell_ids
log = logging.getLogger(__name__)


class Pokestopper(Normal):
    def inicialise(self):
        log.info('Точечное сканирование P\S, переопределяем переменные БД')
        self.scanner.mode.step = 0.0015
        self.scanner.mode.walk = 6

        self.scanner.mode.is_catch = False
        self.scanner.mode.is_farm = True
        self.scanner.mode.is_lookup = False
        self.scanner.mode.is_defender = False

    def take_step(self):
        position = [self.origin_lat, self.origin_lon, 0]
        coords = self.generate_coords(self.origin_lat, self.origin_lon, self.step, self.distance)

        self.metrica.take_position(position, self.geolocation.get_google_polilyne(coords))
        self.api.set_position(*position)

        step = 1
        for coord in coords:
            self.metrica.take_status(scanner_msg='Point P\S ({} / {})'.format(step, len(coords)))
            log.info('Точечное сканирование P\S ({} / {})'.format(step, len(coords)))

            position = (coord['lat'], coord['lng'], 0)
            if self.walk > 0:
                self._walk_to(self.walk, *position)
            else:
                self.api.set_position(*position)
                self.ai.heartbeat()

            self._work_at_position(position[0], position[1], position[2], seen_pokemon=False, seen_pokestop=True, seen_gym=False, data=coord['id'])
            action_delay(self.ai.delay_action_min, self.ai.delay_action_max)
            step += 1


    def _walk_to(self, speed, lat, lng, alt):
        dist = distance(self.api._position_lat, self.api._position_lng, lat, lng)
        steps = (dist + 0.0) / (speed + 0.0)  # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps

        log.info('Бежим из ' + str((self.api._position_lat, self.api._position_lng)) + " в " + str(str((lat, lng))) +
                   " на " + str(round(dist, 2)) + " по прямой. " + str(format_time(ceil(steps))))

        if steps != 0:
            dLat = (lat - self.api._position_lat) / steps
            dLng = (lng - self.api._position_lng) / steps

            for i in range(intSteps):
                cLat = self.api._position_lat + dLat + random_lat_long_delta()
                cLng = self.api._position_lng + dLng + random_lat_long_delta()

                self.api.set_position(cLat, cLng, alt)
                self.ai.heartbeat()

                action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

        self.api.set_position(lat, lng, alt)
        self.ai.heartbeat()


    def _work_at_position(self, lat, lng, alt, seen_pokemon=False, seen_pokestop=False, seen_gym=False, data=None):
        if data is not None:
            pokestop = self.session.query(Pokestop).get(data)
            cell = {
                'forts': [
                    {
                        'id': pokestop.id,
                        'type': 1,
                        'latitude': pokestop.latitude,
                        'longitude': pokestop.longitude
                     }
                ]
            }

            self.metrica.take_search({'pokestops': 1})

            self.api.set_position(lat, lng, alt)
            self.ai.work_on_cell(cell, (lat, lng, alt),  seen_pokemon=False,  seen_pokestop=True, seen_gym=False)


            position = (lat, lng, alt)
            cellid = get_cell_ids(lat, lng)
            timestamp = [0, ] * len(cellid)
            map_cells = list()

            sleep(self.ai.delay_scan)
            response_dict = self.api.get_map_objects(latitude=f2i(lat), longitude=f2i(lng),  since_timestamp_ms=timestamp, cell_id=cellid)

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

            self.api.set_position(lat, lng, alt)

            for cell in map_cells:
                self.ai.work_on_cell(cell, position,  seen_pokemon=seen_pokemon,  seen_pokestop=seen_pokestop, seen_gym=seen_gym)



    def generate_coords(self, latitude, longitude, step_size, distance):
        sql = """
            SELECT
                id as "pokestop_id",
                latitude as "pokestop_latitude",
                longitude as "pokestop_longitude",
                (
                6371 * acos (
                  cos ( radians({0}) )
                  * cos( radians( latitude ) )
                  * cos( radians( longitude ) - radians({1}) )
                  + sin ( radians({2}) )
                  * sin( radians( latitude ) )
                ) * 1000
              ) AS "pokestop_distance"
            FROM pokestop
            HAVING pokestop_distance < {3}
            ORDER BY pokestop_distance

        """.format(latitude, longitude, latitude, distance)

        coords = []

        for pokestop in self.session.execute(sql_text(sql)):
            lat = pokestop[1] + random_lat_long_delta()
            lng = pokestop[2] + random_lat_long_delta()

            coords.append({'lat': lat, 'lng': lng, 'id': pokestop[0]})

        return coords