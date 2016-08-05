# -*- coding: utf-8 -*-
import logging
import random
from math import ceil
from sqlalchemy import text as sql_text
from Interfaces.MySQL.Schema import Gym
from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Stepper.Normal import Normal
from Interfaces.AI.Worker.Utils import i2f, format_time, encode_coords, distance, format_dist

from Interfaces.pgoapi.utilities import f2i, h2f

log = logging.getLogger(__name__)


class Gymmer(Normal):
    def inicialise(self):
        log.info('Точечное сканирование GYM, переопределяем переменные БД')
        self.scanner.mode.step = 0.0015
        self.scanner.mode.walk = 90
        self.scanner.mode.is_catch = 0
        self.scanner.mode.is_farm = 0
        self.scanner.mode.is_lookup = 1
        self.scanner.mode.is_defender = 0

        self.scanner.location.distance = 20

        self.session.commit()

    def take_step(self):
        position = [self.origin_lat, self.origin_lon, 0]
        coords = self.generate_coords(self.origin_lat, self.origin_lon, self.step, self.distance)

        self.metrica.take_position(position, self.geolocation.get_google_polilyne(coords))
        self.api.set_position(*position)

        step = 1
        for coord in coords:
            self.metrica.take_status(scanner_msg='Точечное сканирование GYM ({} / {})'.format(step, len(coords)))
            log.info('Точечное сканирование GYM ({} / {})'.format(step, len(coords)))

            position = (coord['lat'], coord['lng'], 0)
            if self.walk > 0:
                self._walk_to(self.walk, *position)
            else:
                self.api.set_position(*position)
            sleep(1)
            self._work_at_position(position[0], position[1], position[2], seen_pokemon=False, seen_pokestop=False, seen_gym=True, data=coord['id'])
            sleep(1)
            step += 1


    def _walk_to(self, speed, lat, lng, alt):
        dist = distance(i2f(self.api._position_lat), i2f(self.api._position_lng), lat, lng)
        steps = (dist + 0.0) / (speed + 0.0)  # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps

        log.info('Бежим из ' + str((i2f(self.api._position_lat), i2f(self.api._position_lng))) + " в " + str(str((lat, lng))) +
                   " на " + str(round(dist, 2)) + " по прямой. " + str(format_time(ceil(steps))))

        if steps != 0:
            dLat = (lat - i2f(self.api._position_lat)) / steps
            dLng = (lng - i2f(self.api._position_lng)) / steps

            for i in range(intSteps):
                cLat = i2f(self.api._position_lat) + dLat + random_lat_long_delta()
                cLng = i2f(self.api._position_lng) + dLng + random_lat_long_delta()
                self.api.set_position(cLat, cLng, alt)
                self.ai.heartbeat()

                sleep(1)
            self.api.set_position(lat, lng, alt)
            self.ai.heartbeat()



    def _work_at_position(self, lat, lng, alt, seen_pokemon=False, seen_pokestop=False, seen_gym=False, data=None):
        if data is not None:
            gym = self.session.query(Gym).get(data)
            cell = {
                'forts': [
                    {
                        'id': gym.id,
                        'owned_by_team': 4,
                        'gym_points': 1,
                        'latitude': gym.latitude,
                        'longitude': gym.longitude
                     }
                ]
            }

            sleep(5)
            self.api.set_position(lat, lng, alt)
            self.ai.work_on_cell(cell, (lat, lng, alt),  seen_pokemon=False,  seen_pokestop=False, seen_gym=True)
        else:
            sleep(5)


    def generate_coords(self, latitude, longitude, step_size, distance):
        sql = """
            SELECT
                id as "gym_id",
                latitude as "gym_latitude",
                longitude as "gym_longitude",
                (
                3959 * acos (
                  cos ( radians({0}) )
                  * cos( radians( latitude ) )
                  * cos( radians( longitude ) - radians({1}) )
                  + sin ( radians({2}) )
                  * sin( radians( latitude ) )
                ) * 1000
              ) AS "gym_distance"
            FROM gym
            HAVING gym_distance < {3}
            ORDER BY gym_distance

        """.format(latitude, longitude, latitude, distance)

        coords = []

        for gym in self.session.execute(sql_text(sql)):
            lat = gym[1] + random.uniform(-step_size, step_size)
            lng = gym[2] + random.uniform(-step_size, step_size)

            coords.append({'lat': lat, 'lng': lng, 'id': gym[0]})

        return coords

