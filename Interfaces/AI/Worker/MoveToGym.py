# -*- coding: utf-8 -*-

import logging

from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Worker.Utils import distance, format_dist

log = logging.getLogger(__name__)


class MoveToGym(object):
    def __init__(self, gym, ai):
        self.gym = gym
        self.api = ai.api
        self.ai = ai
        self.stepper = ai.stepper
        self.position = ai.position
        self.scanner = ai.scanner

    def work(self):
        lat = self.gym['latitude']
        lng = self.gym['longitude']
        gym_id = self.gym['id']
        dist = distance(self.position[0], self.position[1], lat, lng)

        log.info('[#] Видим GYM {} на удалении {}'.format(gym_id, format_dist(dist)))

        if dist > 10:
            log.info('[#] GYM дальше 10 метров, бежим...')
            position = (lat, lng, 0.0)

            if self.scanner.mode.walk > 0:
                self.stepper._walk_to(self.scanner.mode.walk, *position)
            else:
                self.api.set_position(*position)

            self.api.player_update(latitude=lat, longitude=lng)
            self.position = position
            response_dict = self.api.call()
            log.info('[#] Прибыли к GYM\'у')
            sleep(2)
            return response_dict

        return None

