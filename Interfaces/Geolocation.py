#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import re

from geopy.geocoders import GoogleV3

class Geolocation():
    def __init__(self, config):
        self.config = config

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
