# -*- coding: utf-8 -*-
import logging
import math

from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Stepper.Normal import Normal
from Interfaces.AI.Worker.Utils import encode_coords, distance, format_dist
log = logging.getLogger(__name__)


class Starline(Normal):
    def take_step(self):
        position = [self.origin_lat, self.origin_lon, 0]
        coords = self.generate_coords(self.origin_lat, self.origin_lon, self.step, self.distance)

        self.get_google_path(coords)
        self.api.set_position(*position)

        step = 1
        for coord in coords:
            # starting at 0 index
            self.scanner_thread._status_scanner_apply(1, 'Звездное сканирование ({} / {})'.format(step, len(coords)))

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
    def generate_coords(latitude, longitude, step_size, distance_limit):
        coords = [{'lat': latitude, 'lng': longitude}]

        for coord in Starline.generate_location_steps([latitude, longitude]):
            lat = coord[0]
            lng = coord[1]

            coords.append({'lat': lat, 'lng': lng})

            if distance(latitude, longitude, lat, lng) > distance_limit:
                break

        return coords

    @staticmethod
    def get_new_coords(init_loc, distance, bearing):
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
    def generate_location_steps(initial_loc):
        #Bearing (degrees)
        NORTH = 0
        EAST = 90
        SOUTH = 180
        WEST = 270

        pulse_radius = 0.1                  # km - radius of players heartbeat is 100m
        xdist = math.sqrt(3)*pulse_radius   # dist between column centers
        ydist = 3*(pulse_radius/2)          # dist between row centers

        yield (initial_loc[0], initial_loc[1], 0) #insert initial location

        ring = 1
        loc = initial_loc
        while True:
            #Set loc to start at top left
            loc = Starline.get_new_coords(loc, ydist, NORTH)
            loc = Starline.get_new_coords(loc, xdist / 2, WEST)
            for direction in range(6):
                for i in range(ring):
                    if direction == 0: # RIGHT
                        loc = Starline.get_new_coords(loc, xdist, EAST)
                    if direction == 1: # DOWN + RIGHT
                        loc = Starline.get_new_coords(loc, ydist, SOUTH)
                        loc = Starline.get_new_coords(loc, xdist / 2, EAST)
                    if direction == 2: # DOWN + LEFT
                        loc = Starline.get_new_coords(loc, ydist, SOUTH)
                        loc = Starline.get_new_coords(loc, xdist / 2, WEST)
                    if direction == 3: # LEFT
                        loc = Starline.get_new_coords(loc, xdist, WEST)
                    if direction == 4: # UP + LEFT
                        loc = Starline.get_new_coords(loc, ydist, NORTH)
                        loc = Starline.get_new_coords(loc, xdist / 2, WEST)
                    if direction == 5: # UP + RIGHT
                        loc = Starline.get_new_coords(loc, ydist, NORTH)
                        loc = Starline.get_new_coords(loc, xdist / 2, EAST)
                    yield (loc[0], loc[1], 0)
            ring += 1
