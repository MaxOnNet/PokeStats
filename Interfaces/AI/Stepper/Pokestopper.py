# -*- coding: utf-8 -*-
import logging
import random
from math import ceil
from sqlalchemy import text as sql_text
from Interfaces.MySQL.Schema import Pokestop
from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Stepper.Normal import Normal
from Interfaces.AI.Worker.Utils import format_time, distance

log = logging.getLogger(__name__)


class Pokestopper(Normal):
    def inicialise(self):
        log.info('Точечное сканирование P\S, переопределяем переменные БД')
        self.scanner.mode.step = 0.0015
        self.scanner.mode.walk = 25

        self.scanner.mode.is_catch = False
        self.scanner.mode.is_farm = True
        self.scanner.mode.is_lookup = False
        self.scanner.mode.is_defender = False

        self.session.commit()

    def take_step(self):
        position = [self.origin_lat, self.origin_lon, 0]
        coords = self.generate_coords(self.origin_lat, self.origin_lon, self.step, self.distance)

        self.metrica.take_position(position, self.geolocation.get_google_polilyne(coords))
        self.api.set_position(*position)

        step = 1
        for coord in coords:
            self.metrica.take_status(scanner_msg='Точечное сканирование P\S ({} / {})'.format(step, len(coords)))
            log.info('Точечное сканирование P\S ({} / {})'.format(step, len(coords)))

            position = (coord['lat'], coord['lng'], 0)
            if self.walk > 0:
                self._walk_to(self.walk, *position)
            else:
                self.api.set_position(*position)
            sleep(1)
            self._work_at_position(position[0], position[1], position[2], seen_pokemon=False, seen_pokestop=True, seen_gym=False, data=coord['id'])
            sleep(1)
            step += 1


    def _walk_to(self, speed, lat, lng, alt):
        dist = distance(self.api._position_lat, self.api._position_lng, lat, lng)
        steps = (dist + 0.0) / (speed + 0.0)  # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps

        log.info('Бежим из ' + str(self.api._position_lat) +", " + str(self.api._position_lng) + " в " + str(str((lat, lng))) +
                   " на " + str(round(dist, 2)) + " по прямой. " + str(format_time(ceil(steps))))

        if steps != 0:
            dLat = (lat - self.api._position_lat) / steps
            dLng = (lng - self.api._position_lng) / steps

            for i in range(intSteps):
                cLat = self.api._position_lat + dLat + random_lat_long_delta()
                cLng = self.api._position_lng + dLng + random_lat_long_delta()

                self.api.set_position(cLat, cLng, alt)

                sleep(1)

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

            sleep(5)
            self.api.set_position(lat, lng, alt)
            self.ai.work_on_cell(cell, (lat, lng, alt),  seen_pokemon=False,  seen_pokestop=True, seen_gym=False)
        else:
            sleep(5)


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