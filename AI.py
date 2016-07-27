#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import random
import threading
import time
from random import randint

from google.protobuf.internal import encoder
from s2sphere import CellId, LatLng

from Interfaces.Config import Config
from Interfaces.Geolocation import Geolocation
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import Scanner as dbScanner
from Interfaces.MySQL.Schema import parse_map

from Interfaces.pgoapi.utilities import f2i
from Interfaces.pgoapi import PGoApi

from AI.Profile import Profile

class AI:
    def __init__(self):
        self.config = Config()

        self.position_latitude = self.config_xml.get("AI", "location", "latitude", "55.0467")
        self.position_longitude = self.config_xml.get("AI", "location", "longitude", "55.0467")
        self.position = [self.position_latitude, self.position_longitude]


        self.api = PGoApi()

    def _login(self):
        self.account_service = self.config.get("AI", "config", "service", "ptc")
        self.account_username = self.config.get("AI", "config", "username", "")
        self.account_password = self.config.get("AI", "config", "password", "")

        self.api.set_position(*self.position)
        self.api.login(self.account_service, self.account_username, self.account_password)
