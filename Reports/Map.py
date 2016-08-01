#!/usr/bin/python
# -*- coding: utf-8 -*-

import calendar
import time
import sqlalchemy

from flask import Flask, jsonify, render_template, request
from flask.json import JSONEncoder


from datetime import datetime

from Interfaces.Config import Config
from Interfaces.MySQL import init_fast as init
from Interfaces.MySQL.Schema import PokemonSpawnpoint, Gym, Pokestop, Pokemon, Scanner, ScannerStatistic, ScannerLocation


# Reports
from Reports.Trainers.Top import Top as ReportTrainerTop
from Reports.Gyms.Top import Top as ReportGymTop
from Reports.Gyms.Team import Team as ReportGymTeam
from Reports.Pokemons.Average import Average as ReportPokemonAverage
from Reports.Pokemons.Now import Now as ReportPokemonNow

from Reports.Servers.Average import Average as ReportServerAverage

from . import config

class Map(Flask):
    def __init__(self, import_name, **kwargs):
        super(Map, self).__init__(import_name, **kwargs)

        self.config_xml = Config()
        self.json_encoder = CustomJSONEncoder
        self.route("/", methods=['GET'])(self.index)
        self.route("/next_loc", methods=['POST'])(self.next_loc)

        self._flask_json()
        self._flask_report()

        self.conf_latitude = self.config_xml.get("map", "", "latitude", "55.0467")
        self.conf_longitude = self.config_xml.get("map", "", "longitude", "73.3111")
        self.pos_gmapkey = self.config_xml.get("map", "google", "key", "")

        # init dicts
        self.dict_pokemons = []
        self.dict_pokestats = []
        self.dict_gyms = []
        self.dict_scanners = []
        self.dict_timestamp = 0

    def _flask_report(self):
        # trainers
        self.add_url_rule("/report/trainer/top", view_func=ReportTrainerTop.as_view("report/trainer/top", config=self.config_xml))

        # Gyms
        self.add_url_rule("/report/gym/top", view_func=ReportGymTop.as_view("report/gym/top", config=self.config_xml))
        self.add_url_rule("/report/gym/team", view_func=ReportGymTeam.as_view("report/gym/team", config=self.config_xml))

        # Pokemon
        self.add_url_rule("/report/pokemon/average", view_func=ReportPokemonAverage.as_view("report/pokemon/average", config=self.config_xml))
        self.add_url_rule("/report/pokemon/now", view_func=ReportPokemonNow.as_view("report/pokemon/now", config=self.config_xml))

        # Servers
        self.add_url_rule("/report/server/average", view_func=ReportServerAverage.as_view("report/server/average", config=self.config_xml))

    def _flask_json(self):
        self.route("/raw_data", methods=['GET'])(self.json_raw)

    def _database_fetch(self):
        # Cache 10 sec
        if self.dict_timestamp + 10 < time.time():

            session_maker = init(self.config_xml)
            session_mysql = session_maker()

            self.dict_pokemons = []
            self.dict_pokestats = []
            self.dict_gyms = []
            self.dict_scanners = []
            try:
                for pokemon_spawnpoint in PokemonSpawnpoint.get_active(session_mysql).all():
                    pokemon_dict = pokemon_spawnpoint.__dict__
                    try:
                        pokemon_db = session_mysql.query(Pokemon).filter(Pokemon.id == pokemon_spawnpoint.cd_pokemon).one()
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

                    self.dict_pokemons.append(pokemon_dict)

                for scanner in session_mysql.query(Scanner).filter(Scanner.is_enable).all():
                    scanner_dict = scanner.__dict__

                    scanner_dict['latitude'] = scanner.location.latitude
                    scanner_dict['longitude'] = scanner.location.longitude

                    scanner_dict['count_pokemons'] = scanner.statistic.pokemons
                    scanner_dict['count_pokestops'] = scanner.statistic.pokestops
                    scanner_dict['count_gyms'] = scanner.statistic.gyms
                    scanner_dict['date_start'] = scanner.statistic.date_start
                    scanner_dict['date_change'] = scanner.statistic.date_change

                    self.dict_scanners.append(scanner_dict)

                self.dict_pokestops = [u.__dict__ for u in session_mysql.query(Pokestop).all()]
                self.dict_gyms = [u.__dict__ for u in session_mysql.query(Gym).all()]

                self.dict_timestamp = time.time()
            finally:
                session_mysql.flush()
                session_mysql.expunge_all()
                session_mysql.close()

    def index(self):
        if request.args.get('latitude') and request.args.get('longitude'):
            pos_latitude = request.args.get('latitude')
            pos_longitude = request.args.get('longitude')
        else:
            pos_latitude = self.conf_latitude
            pos_longitude = self.conf_longitude

        return render_template('map.html',
                               lat=pos_latitude,
                               lng=pos_longitude,
                               gmaps_key=self.pos_gmapkey)


    def json_raw(self):
        self._database_fetch()

        json_dict = {
            "scanned": [],
            "gyms": [],
            "pokestops": [],
            "pokemons": []
        }

        # use geo filter
        if request.args.get('latitude') and request.args.get('longitude'):
            pass

        if request.args.get('pokemon') == "true":
            json_dict['pokemons'] = self.dict_pokemons

        if request.args.get('pokestops') == "true":
            json_dict['pokestops'] = self.dict_pokestops

        if request.args.get('gyms') == "true":
            json_dict['gyms'] = self.dict_gyms

        if request.args.get('scanned') == "true":
            json_dict['scanned'] = self.dict_scanners

        return jsonify(json_dict)



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
