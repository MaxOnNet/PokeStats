# -*- coding: utf-8 -*-
import logging


from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Stepper.Normal import Normal

log = logging.getLogger(__name__)


class Spiral(Normal):
    def take_step(self):
        position = [self.origin_lat, self.origin_lon]
        self.api.set_position(*position)

        step = 1
        for coord in self.generate_spiral(self.origin_lat, self.origin_lon, 0.0009, self.steplimit2):
            # starting at 0 index
            self.scanner_thread._status_scanner_apply(1, '[AI] Scanning area for objects ({} / {})'.format((step + 1), self.steplimit**2))

            log.debug('steplimit: {} x: {} y: {} pos: {} dx: {} dy {}'.format(
                        self.steplimit2, self.x, self.y, self.pos, self.dx,self.dy))

            position = (coord['lat'], coord['lng'], 0)

            if self.walk > 0:
                self._walk_to(self.walk, *position)
            else:
                self.api.set_position(*position)

            self._work_at_position(position[0], position[1], position[2], True)
            sleep(10*self.scanner.mode.is_human_sleep)
            step += 1

    @staticmethod
    def generate_spiral(latitude, longitude, step_size, step_limit):
        coords = [{'lat': latitude, 'lng': longitude}]
        steps, x, y, d, m = 1, 0, 0, 1, 1

        while steps < step_limit:
            while 2 * x * d < m and steps < step_limit:
                x += d
                steps += 1
                lat = x * step_size + latitude + random_lat_long_delta()
                lng = y * step_size + longitude + random_lat_long_delta()
                coords.append({'lat': lat, 'lng': lng})
            while 2 * y * d < m and steps < step_limit:
                y += d
                steps += 1
                lat = x * step_size + latitude + random_lat_long_delta()
                lng = y * step_size + longitude + random_lat_long_delta()
                coords.append({'lat': lat, 'lng': lng})

            d *= -1
            m += 1
        return coords