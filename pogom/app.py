#!/usr/bin/python
# -*- coding: utf-8 -*-

import calendar
from flask import Flask, jsonify, render_template
from flask.json import JSONEncoder
from datetime import datetime

from Interfaces.Config import Config
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import PokemonSpawnpoint, Gym, Pokestop

from . import config


class Pogom(Flask):
    def __init__(self, import_name, **kwargs):
        super(Pogom, self).__init__(import_name, **kwargs)
        self.json_encoder = CustomJSONEncoder
        self.route("/", methods=['GET'])(self.fullmap)
        self.route("/pokemons", methods=['GET'])(self.pokemons)
        self.route("/gyms", methods=['GET'])(self.gyms)
        self.route("/pokestops", methods=['GET'])(self.pokestops)
        self.route("/raw_data", methods=['GET'])(self.raw_data)

        self.config_xml = Config()

        self._init_database()

    def _init_database(self):
        self.session_maker = init(self.config_xml)
        self.session_mysql = self.session_maker()


    def fullmap(self):
        return render_template('map.html',
                               lat=config['ORIGINAL_LATITUDE'],
                               lng=config['ORIGINAL_LONGITUDE'],
                               gmaps_key=config['GMAPS_KEY'])

    # Добавить возможность учитывать регион иначе браузер повещается
    def get_raw_data(self):
        return {
            'gyms': [u.__dict__ for u in self.session_mysql.query(Gym).all()],
            'pokestops': [u.__dict__ for u in self.session_mysql.query(Pokestop).all()],
            'pokemons': [u.__dict__ for u in PokemonSpawnpoint.get_active(self.session_mysql).all()]
        }

    def raw_data(self):
        return jsonify(self.get_raw_data())

    def pokemons(self):
        return jsonify(self.get_raw_data()['pokemons'])

    def pokestops(self):
        return jsonify(self.get_raw_data()['pokestops'])

    def gyms(self):
        return jsonify(self.get_raw_data()['gyms'])


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                if obj.utcoffset() is not None:
                    obj = obj - obj.utcoffset()
                millis = int(
                    calendar.timegm(obj.timetuple()) * 1000 +
                    obj.microsecond / 1000
                )
                return millis
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
