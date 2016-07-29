import logging

from Interfaces.AI.Human import sleep
from Interfaces.AI.Worker.Utils import distance, format_dist

log = logging.getLogger(__name__)


class MoveToPokestop(object):
    def __init__(self, pokestop, ai):
        self.pokestop = pokestop
        self.api = ai.api
        self.stepper = ai.stepper
        self.position = ai.position
        self.scanner = ai.scanner

    def work(self):
        lat = self.pokestop['latitude']
        lng = self.pokestop['longitude']
        pokestop_id = self.pokestop['id']

        dist = distance(self.position[0], self.position[1], lat, lng)

        log.info('[#] Found pokestop {} at distance {}'.format(pokestop_id, format_dist(dist)))

        if dist > 10:
            log.info('[#] Need to move closer to Pokestop')
            position = (lat, lng, 0.0)

            if self.scanner.location.walk > 0:
                self.stepper._walk_to(self.scanner.location.walk, *position)
            else:
                self.api.set_position(*position)

            self.api.player_update(latitude=lat, longitude=lng)
            response_dict = self.api.call()
            log.info('[#] Arrived at Pokestop')
            sleep(2)
            return response_dict

        return None
