#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import re

from geopy.geocoders import GoogleV3
from Interfaces.AI.Worker.Utils import distance, i2f, format_time, encode_coords

class Geolocation():
    def __init__(self, thread):
        self.config = thread.config

    def get_position_by_name(self, location_name):
        prog = re.compile("^(\-?\d+\.\d+)?,\s*(\-?\d+\.\d+?)$")
        res = prog.match(location_name)
        if res:
            latitude, longitude, altitude = float(res.group(1)), float(res.group(2)), 0
        else:
            geolocator = GoogleV3(api_key=self.config.get("map", "google", "key", ""))
            loc = geolocator.geocode(location_name)
            latitude, longitude, altitude = loc.latitude, loc.longitude, loc.altitude

        return (latitude, longitude, altitude)


    def get_google_polilyne(self, coords):
        return 'http://maps.googleapis.com/maps/api/staticmap?size=400x400&apikey={1}&path=enc:{0}'.format(encode_coords(coords), self.config.get("map", "google", "key", ""))

