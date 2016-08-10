# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import pprint

import logging

from math import ceil, sqrt
from s2sphere import CellId, LatLng
from google.protobuf.internal import encoder

from Interfaces import analyticts_timer
from Interfaces.AI.Human import sleep, random_lat_long_delta, action_delay
from Interfaces.AI.Worker.Utils import distance, i2f, format_time, encode_coords
from Interfaces.MySQL.Schema import parse_map_cell

from Interfaces.pgoapi.utilities import f2i, h2f, get_cell_ids


def _pythagorean(lat, lng):
    return sqrt((lat ** 2) + (lng ** 2))


def get_google_polilyne(coords):
    return 'http://maps.googleapis.com/maps/api/staticmap?size=400x400&apikey={1}&path=enc:{0}'.format(encode_coords(coords), "AIzaSyA3OUM5s1t1mX3mqtSMNSToPD_uaTAdP3M")

init_lat = 55.0467
init_lng = 73.3111

dest_lat = 55.0306
dest_lng = 73.3305
walk_speed = 50
walk_coords = []


walk_distance = distance(init_lat, init_lng, dest_lat, dest_lng)
walk_distance_total = max(1, walk_distance)
walk_steps = (walk_distance + 0.0) / (walk_speed + 0.0)

if walk_distance < walk_speed or int(walk_steps) <= 1:
    delta_lat = 0
    delta_lng = 0
    magnitude = 0
else:
    delta_lat = (dest_lat - init_lat) / int(walk_steps)
    delta_lng = (dest_lng - init_lng) / int(walk_steps)
    magnitude = _pythagorean(delta_lat, delta_lng)

print "Бежим из [{}, {}] в [{}, {}] на расстояние {}, со скоростью {},  в {} шагов".format(init_lat, init_lng, dest_lat, dest_lng, round(walk_distance, 2), walk_speed, round(walk_steps))

if (delta_lat == 0 and delta_lng == 0) or walk_distance < walk_speed:
    print "Дистанция слишком мала"
    sys.exit(0)


q = 1
w = 1
e = 1

x = q & w & e
print x
sys.exit(0)
while True:
    total_delta_step = walk_distance/int(walk_steps)
    total_delta_lat = (dest_lat - init_lat)
    total_delta_lng = (dest_lng - init_lng)
    magnitude = _pythagorean(total_delta_lat, total_delta_lng)

    if distance(init_lat, init_lng, dest_lat, dest_lng) <= total_delta_step:
        print "Прибыли в [{}, {}] разрыв {}".format(dest_lat, dest_lng, distance(init_lat, init_lng, dest_lat, dest_lng))
        print get_google_polilyne(walk_coords)
        break

    unit_lat = delta_lat / magnitude
    unit_lng = delta_lng / magnitude

    scaled_delta_lat = unit_lat * magnitude
    scaled_delta_lng = unit_lng * magnitude

    c_lat = init_lat + scaled_delta_lat + random_lat_long_delta()

    c_lng = init_lng + scaled_delta_lng + random_lat_long_delta()
    walt_step_distance = distance(init_lat, init_lng, c_lat, c_lng)
    print "Мы в [{}, {}], прошли {}".format(c_lat, c_lng,  walt_step_distance)
    walk_coords.append({"lat": c_lat, "lng": c_lng})
    init_lat = c_lat
    init_lng = c_lng

