#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask.json import JSONEncoder
from flask_cache import Cache

import sqlalchemy
from sqlalchemy import text as sql_text

from Interfaces.Config import Config
from Interfaces.MySQL import init_fast as init
from Interfaces.MySQL.Schema import PokemonSpawnpoint, Gym, Pokestop, Pokemon, Scanner, ScannerStatistic, ScannerLocation


class Report:
    def __init__(self, config, template, cache_time=60):
        self.config = config
        self.template = template
        self.data = []

    def _database_init(self):
        self.session_maker = init(self.config)
        self.session_mysql = self.session_maker()

    def _database_execute(self, sql):
        return self.session_mysql.execute(sql_text(sql))

    def _database_close(self):
        self.session_mysql.flush()
        self.session_mysql.expunge_all()
        self.session_mysql.close()

    def _prepare_data(self):
        pass

    def render(self):
        time_s = time.time()
        try:
            self._database_init()
            try:

                self._prepare_data()
            finally:
                self._database_close()
        finally:
            pass

        time_e = time.time()
        time_d = (time_e - time_s)

        return render_template(self.template, table=self.data, duration=time_d)
