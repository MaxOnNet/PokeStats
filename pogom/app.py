#!/usr/bin/python
# -*- coding: utf-8 -*-

import calendar
from flask import Flask, jsonify, render_template, request
from flask.json import JSONEncoder
from datetime import datetime

from Interfaces.Config import Config
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import PokemonSpawnpoint, Gym, Pokestop, Pokemon
import sqlalchemy
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



    def _database_init(self):
        self.session_maker = init(self.config_xml)
        self.session_mysql = self.session_maker()

    def _database_close(self):
        self.session_mysql.flush()
        self.session_mysql.expunge_all()
        self.session_mysql.close()

    def fullmap(self):
        return render_template('map.html',
                               lat=config['ORIGINAL_LATITUDE'],
                               lng=config['ORIGINAL_LONGITUDE'],
                               gmaps_key=config['GMAPS_KEY'])

    # Добавить возможность учитывать регион иначе браузер повещается
    def get_raw_data(self):
        self._database_init()
        dict_podemons = []

        for pokemon_spawnpoint in PokemonSpawnpoint.get_active(self.session_mysql).all():
            pokemon_dict = pokemon_spawnpoint.__dict__
            try:
                pokemon_db = self.session_mysql.query(Pokemon).filter(Pokemon.id == pokemon_spawnpoint.cd_pokemon).one()
                if pokemon_db:
                    pokemon_dict['pokemon_name'] = pokemon_db.name
                    pokemon_dict['pokemon_group'] = pokemon_db.group
                    pokemon_dict['pokemon_color'] = pokemon_db.color
                    pokemon_dict['pokemon_zoom'] = pokemon_db.zoom
                else:
                    pokemon_dict['pokemon_name'] = 'NoName'
                    pokemon_dict['pokemon_group'] = 'NoGroup'
                    pokemon_dict['pokemon_color'] = '#000000'
                    pokemon_dict['pokemon_zoom'] = 1

            except:
                pokemon_dict['pokemon_name'] = 'NoName'
                pokemon_dict['pokemon_group'] = 'NoGroup'
                pokemon_dict['pokemon_color'] = '#000000'
                pokemon_dict['pokemon_zoom'] = 1


            dict_podemons.append(pokemon_dict)

        dict = {
            'gyms': [u.__dict__ for u in self.session_mysql.query(Gym).all()],
            'pokestops': [u.__dict__ for u in self.session_mysql.query(Pokestop).all()],
            'pokemons': dict_podemons
        }

        self._database_close()

        return dict

    def raw_data(self):
        dict=self.get_raw_data()

        if request.args.get('pokemon') == "false":
            dict['pokemons'] = ""

        if request.args.get('pokestops') == "false":
            dict['pokestops'] = ""

        if request.args.get('gyms') == "false":
            dict['gyms'] = ""

        return jsonify(dict)


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

            if isinstance(obj, sqlalchemy.orm.state.InstanceState):
                return ""

            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
