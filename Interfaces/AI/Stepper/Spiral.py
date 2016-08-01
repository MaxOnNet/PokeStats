# -*- coding: utf-8 -*-
import logging
import math

from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Stepper.Normal import Normal
from Interfaces.AI.Worker.Utils import encode_coords, distance, format_dist
log = logging.getLogger(__name__)


class Spiral(Normal):
    def take_step(self):
        position = [self.origin_lat, self.origin_lon, 0]
        coords = self.generate_spiral_arhimed(self.origin_lat, self.origin_lon, 0.001, self.distance)

        self.get_google_path(coords)
        self.api.set_position(*position)

        step = 1
        for coord in coords:
            # starting at 0 index
            self.scanner_thread._status_scanner_apply(1, 'Спиральное сканирование ({} / {})'.format(step, len(coords)))

            position = (coord['lat'], coord['lng'], 0)

            if self.walk > 0:
                self._walk_to(self.walk, *position)
            else:
                self.api.set_position(*position)
            sleep(1)
            self._work_at_position(position[0], position[1], position[2], seen_pokemon=True, seen_pokestop=True, seen_gym=True)

            sleep(10*self.scanner.mode.is_human_sleep)
            step += 1


    @staticmethod
    def generate_spiral_arhimed(latitude, longitude, step_size, distance_limit):
        coords = [{'lat': latitude, 'lng': longitude}]

        for coord in Spiral.spiral_points(step_size, step_size):
            lat = latitude + coord[0] + random_lat_long_delta()
            lng = longitude + coord[1] + random_lat_long_delta()

            coords.append({'lat': lat, 'lng': lng})

            if distance(latitude, longitude, lat, lng) > distance_limit:
                break

        return coords


    @staticmethod
    def spiral_points(arc=1, separation=1):
        """generate points on an Archimedes' spiral
        with `arc` giving the length of arc between two points
        and `separation` giving the distance between consecutive
        turnings
        - approximate arc length with circle arc at given distance
        - use a spiral equation r = b * phi
        """
        def p2c(r, phi):
            """polar to cartesian
            """
            return (r * math.cos(phi), r * math.sin(phi))

        # yield a point at origin
        yield (0, 0)

        # initialize the next point in the required distance
        r = arc
        b = separation / (2 * math.pi)
        # find the first phi to satisfy distance of `arc` to the second point
        phi = float(r) / b
        while True:
            yield p2c(r, phi)
            # advance the variables
            # calculate phi that will give desired arc length at current radius
            # (approximating with circle)
            phi += float(arc) / r
            r = b * phi