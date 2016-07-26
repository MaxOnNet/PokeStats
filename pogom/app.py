#!/usr/bin/python
# -*- coding: utf-8 -*-

import calendar
from flask import Flask, jsonify, render_template, request
from flask.json import JSONEncoder
from flask.views import View

from datetime import datetime

from Interfaces.Config import Config
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import PokemonSpawnpoint, Gym, Pokestop, Pokemon, Scanner, ScannerStatistic, ScannerLocation
import sqlalchemy
from sqlalchemy import text as sql_text
from . import config

from Reports.Gyms.Top import Top as ReportGymTop
from Reports.Pokemons.Average import Average as ReportPokemonAverage
from Reports.Pokemons.Now import Now as ReportPokemonNow

from Reports.Servers.Average import Average as ReportServerAverage
class Pogom(Flask):

    def __init__(self, import_name, **kwargs):
        super(Pogom, self).__init__(import_name, **kwargs)

        self.config_xml = Config()
        self.json_encoder = CustomJSONEncoder
        self.route("/", methods=['GET'])(self.fullmap)

        self.add_url_rule("/report/gym/top", view_func=ReportGymTop.as_view("report/gym/top", config=self.config_xml))
        self.add_url_rule("/report/pokemon/average", view_func=ReportPokemonAverage.as_view("report/pokemon/average", config=self.config_xml))
        self.add_url_rule("/report/pokemon/now", view_func=ReportPokemonNow.as_view("report/pokemon/now", config=self.config_xml))

        self.add_url_rule("/report/server/average", view_func=ReportServerAverage.as_view("report/server/average", config=self.config_xml))


        self.route("/raw_data", methods=['GET'])(self.raw_data)
        self.route("/next_loc", methods=['POST'])(self.next_loc)



    def _database_init(self):
        self.session_maker = init(self.config_xml)
        self.session_mysql = self.session_maker()

    def _database_close(self):
        self.session_mysql.flush()
        self.session_mysql.expunge_all()
        self.session_mysql.close()

    def fullmap(self):
        if request.args.get('latitude') and request.args.get('longitude'):
            config['ORIGINAL_LATITUDE'] = request.args.get('latitude')
            config['ORIGINAL_LONGITUDE'] = request.args.get('longitude')

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

        dict_scanners = []

        for scanner in self.session_mysql.query(Scanner).filter(Scanner.is_enable).all():
            scanner_dict = scanner.__dict__

            scanner_dict['latitude'] = scanner.location.latitude
            scanner_dict['longitude'] = scanner.location.longitude

            scanner_dict['count_pokemons'] = scanner.statistic.pokemons
            scanner_dict['count_pokestops'] = scanner.statistic.pokestops
            scanner_dict['count_gyms'] = scanner.statistic.gyms
            scanner_dict['date_start'] = scanner.statistic.date_start
            scanner_dict['date_change'] = scanner.statistic.date_change

            dict_scanners.append(scanner_dict)

        dict_dict = {
            "scanned": dict_scanners,
            "gyms": [u.__dict__ for u in self.session_mysql.query(Gym).all()],
            "pokestops": [u.__dict__ for u in self.session_mysql.query(Pokestop).all()],
            "pokemons": dict_podemons
        }

        self._database_close()

        return dict_dict

    def raw_data(self):
        dict = self.get_raw_data()

        if request.args.get('pokemon') == "false":
            dict['pokemons'] = []

        if request.args.get('pokestops') == "false":
            dict['pokestops'] = []

        if request.args.get('gyms') == "false":
            dict['gyms'] = []

        if request.args.get('scanned') == "false":
            dict['scanned'] = []

        return jsonify(dict)

    def next_loc(self):
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        if not (lat and lon):
            print('[-] Invalid next location: %s,%s' % (lat, lon))
            return 'bad parameters', 400
        else:
            config['NEXT_LOCATION'] = {'lat': lat, 'lon': lon}
            return 'ok'

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

            if isinstance(obj, ScannerStatistic):
                return ""
            if isinstance(obj, ScannerLocation):
                return ""

            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
