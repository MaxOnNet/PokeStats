# -*- coding: utf-8 -*-
import logging
import math
import random

from Interfaces.AI.Human import sleep, random_lat_long_delta, action_delay
from Interfaces.AI.Stepper.Normal import Normal
from Interfaces.AI.Worker.Utils import encode_coords, distance, format_dist
log = logging.getLogger(__name__)


class Starline(Normal):
    def take_step(self):
        position = [self.origin_lat, self.origin_lon, 0]
        coords = self.generate_coords(self.origin_lat, self.origin_lon, self.step, self.distance)

        self.metrica.take_position(position, self.geolocation.get_google_polilyne(coords))
        self.api.set_position(*position)

        step = 1
        for coord in coords:
            # starting at 0 index
            self.metrica.take_status(scanner_msg='Звездное ({} / {})'.format(step, len(coords)))
            log.info('Звездное сканирование ({} / {})'.format(step, len(coords)))

            position = (coord['lat'], coord['lng'], 0)

            if self.walk > 0:
                self._walk_to(self.walk, *position)
            else:
                self.api.set_position(*position)
                self.ai.heartbeat()

            self._work_at_position(position[0], position[1], position[2], seen_pokemon=True, seen_pokestop=True, seen_gym=True)
            sleep(2)

            step += 1

    @staticmethod
    def generate_coords(latitude, longitude, step_size, distance_limit):
        coords = [{'lat': latitude, 'lng': longitude}]

        for coord in Starline.generate_starline([latitude, longitude], step_size):
            lat = coord[0] + random_lat_long_delta()
            lng = coord[1] + random_lat_long_delta()

            coords.append({'lat': lat, 'lng': lng})

            if distance(latitude, longitude, lat, lng) > distance_limit:
                break

        return coords

    @staticmethod
    def generate_starline_point(init_loc, distance, bearing):
        """ Given an initial lat/lng, a distance(in kms), and a bearing (degrees),
        this will calculate the resulting lat/lng coordinates.
        """
        R = 6378.1 #km radius of the earth
        bearing = math.radians(bearing)

        init_coords = [math.radians(init_loc[0]), math.radians(init_loc[1])] # convert lat/lng to radians

        new_lat = math.asin( math.sin(init_coords[0])*math.cos(distance/R) +
            math.cos(init_coords[0])*math.sin(distance/R)*math.cos(bearing))

        new_lon = init_coords[1] + math.atan2(math.sin(bearing)*math.sin(distance/R)*math.cos(init_coords[0]),
            math.cos(distance/R)-math.sin(init_coords[0])*math.sin(new_lat))

        return [math.degrees(new_lat), math.degrees(new_lon)]


    @staticmethod
    def generate_starline(initial_loc, step_size=0.1):
        #Bearing (degrees)
        NORTH = 0
        EAST = 90
        SOUTH = 180
        WEST = 270

        pulse_radius = step_size * 100               # km - radius of players heartbeat is 100m
        xdist = math.sqrt(3)*pulse_radius   # dist between column centers
        ydist = 3*(pulse_radius/2)          # dist between row centers

        yield (initial_loc[0], initial_loc[1], 0) #insert initial location

        ring = 1
        loc = initial_loc
        while True:
            #Set loc to start at top left
            loc = Starline.generate_starline_point(loc, ydist, NORTH)
            loc = Starline.generate_starline_point(loc, xdist / 2, WEST)
            for direction in range(6):
                for i in range(ring):
                    if direction == 0: # RIGHT
                        loc = Starline.generate_starline_point(loc, xdist, EAST)
                    if direction == 1: # DOWN + RIGHT
                        loc = Starline.generate_starline_point(loc, ydist, SOUTH)
                        loc = Starline.generate_starline_point(loc, xdist / 2, EAST)
                    if direction == 2: # DOWN + LEFT
                        loc = Starline.generate_starline_point(loc, ydist, SOUTH)
                        loc = Starline.generate_starline_point(loc, xdist / 2, WEST)
                    if direction == 3: # LEFT
                        loc = Starline.generate_starline_point(loc, xdist, WEST)
                    if direction == 4: # UP + LEFT
                        loc = Starline.generate_starline_point(loc, ydist, NORTH)
                        loc = Starline.generate_starline_point(loc, xdist / 2, WEST)
                    if direction == 5: # UP + RIGHT
                        loc = Starline.generate_starline_point(loc, ydist, NORTH)
                        loc = Starline.generate_starline_point(loc, xdist / 2, EAST)
                    yield (loc[0], loc[1], 0)
            ring += 1
