# -*- coding: utf-8 -*-
import logging
import random
from math import ceil
from sqlalchemy import text as sql_text
from Interfaces.MySQL.Schema import Gym
from Interfaces.AI.Human import sleep, random_lat_long_delta, action_delay
from Interfaces.AI.Stepper.Normal import Normal
from Interfaces.AI.Worker.Utils import i2f, format_time, encode_coords, distance, format_dist

from Interfaces.pgoapi.utilities import f2i, h2f

log = logging.getLogger(__name__)


class Gymmer(Normal):
    def inicialise(self):
        log.info('Точечное сканирование GYM, переопределяем переменные БД')
        self.scanner.mode.step = 0.0015
        self.scanner.mode.walk = 0

        self.scanner.mode.is_catch = False
        self.scanner.mode.is_farm = False
        self.scanner.mode.is_lookup = True
        self.scanner.mode.is_defender = False

        self.scanner.location.distance = 100

    def take_step(self):
        position = [self.origin_lat, self.origin_lon, 0]
        coords = self.generate_coords(self.origin_lat, self.origin_lon, self.step, self.distance)

        self.metrica.take_position(position, self.geolocation.get_google_polilyne(coords))
        self.api.set_position(*position)

        step = 1
        for coord in coords:
            self.metrica.take_status(scanner_msg='Point GYM ({} / {})'.format(step, len(coords)))
            log.info('Точечное сканирование GYM ({} / {})'.format(step, len(coords)))

            position = (coord['lat'], coord['lng'], 0)
            if self.walk > 0:
                self._walk_to(self.walk, *position)
            else:
                self.api.set_position(*position)
                self.ai.heartbeat()

            self._work_at_position(position[0], position[1], position[2], seen_pokemon=False, seen_pokestop=False, seen_gym=True, data=coord['id'])
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

                sleep(1)

        action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

        self.api.set_position(lat, lng, alt)
        self.ai.heartbeat()



    def _work_at_position(self, lat, lng, alt, seen_pokemon=False, seen_pokestop=False, seen_gym=False, data=None):
        if data is not None:
            gym = self.session.query(Gym).get(data)
            cell = {
                'forts': [
                    {
                        'id': gym.id,
                        'owned_by_team': 0,
                        'gym_points': 1,
                        'latitude': gym.latitude,
                        'longitude': gym.longitude
                     }
                ]
            }

            self.metrica.take_search({'gyms': 1})

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
                6371 * acos (
                  cos ( radians({0}) )
                  * cos( radians( latitude ) )
                  * cos( radians( longitude ) - radians({1}) )
                  + sin ( radians({2}) )
                  * sin( radians( latitude ) )
                ) * 1000
              ) AS "gym_distance"
            FROM gym
            HAVING gym_distance < {3}
            ORDER BY gym_distance ASC
            {4}

        """.format(latitude, longitude, latitude, distance, self.stepper_data)

        coords = []

        for gym in self.session.execute(sql_text(sql)):
            lat = gym[1] + random_lat_long_delta()
            lng = gym[2] + random_lat_long_delta()

            coords.append({'lat': lat, 'lng': lng, 'id': gym[0]})

        return coords

