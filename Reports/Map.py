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
from Reports.Gyms.Membership import Membership as ReportGymMembership
from Reports.Gyms.Top import Top as ReportGymTop
from Reports.Gyms.Team import Team as ReportGymTeam
from Reports.Gyms.Guard import Guard as ReportGymGuard
from Reports.Pokemons.Average import Average as ReportPokemonAverage
from Reports.Pokemons.Now import Now as ReportPokemonNow

from Reports.Servers.Average import Average as ReportServerAverage
from Reports.Servers.Account import Account as ReportServerAccount

from . import config

class Map(Flask):
    def __init__(self, import_name, **kwargs):
        super(Map, self).__init__(import_name, **kwargs)

        self.config_xml = Config()
        self.json_encoder = CustomJSONEncoder
        self.route("/", methods=['GET'])(self.index)

        self._flask_json()
        self._flask_report()

        self.conf_latitude = self.config_xml.get("map", "", "latitude", "55.0467")
        self.conf_longitude = self.config_xml.get("map", "", "longitude", "73.3111")
        self.pos_gmapkey = self.config_xml.get("map", "google", "key", "")

    def _flask_report(self):
        # trainers
        self.add_url_rule("/report/trainer/top", view_func=ReportTrainerTop.as_view("report/trainer/top", config=self.config_xml))

        # Gyms
        self.add_url_rule("/report/gym/membership", view_func=ReportGymMembership.as_view("report/gym/membership", config=self.config_xml))
        self.add_url_rule("/report/gym/top", view_func=ReportGymTop.as_view("report/gym/top", config=self.config_xml))
        self.add_url_rule("/report/gym/team", view_func=ReportGymTeam.as_view("report/gym/team", config=self.config_xml))
        self.add_url_rule("/report/gym/guard", view_func=ReportGymGuard.as_view("report/gym/guard", config=self.config_xml))

        # Pokemon
        self.add_url_rule("/report/pokemon/average", view_func=ReportPokemonAverage.as_view("report/pokemon/average", config=self.config_xml))
        self.add_url_rule("/report/pokemon/now", view_func=ReportPokemonNow.as_view("report/pokemon/now", config=self.config_xml))

        # Servers
        self.add_url_rule("/report/server/average", view_func=ReportServerAverage.as_view("report/server/average", config=self.config_xml))
        self.add_url_rule("/report/server/account", view_func=ReportServerAccount.as_view("report/server/account", config=self.config_xml))
    def _flask_json(self):
        self.route("/put_user_geo", methods=['GET'])(self.json_put_user_geo)
        self.route("/get_data", methods=['GET'])(self.json_get_data)
        self.route("/put_data_geo", methods=['GET'])(self.json_put_data_geo)


    def _database_init(self):
        session_maker = init(self.config_xml)
        session = session_maker()

        return session


    def _database_close(self, session):
        session.flush()
        session.expunge_all()
        session.close()


    def _database_fetch_pokemons(self, session=None, ne_latitude=0, ne_longitude=0, sw_latitude=0, sw_longitude=0):
        pokemons = []

        sql = """
            SELECT
                p.id 	as "id",
                p.name 	as "name",

                ps.latitude	as "latitude",
                ps.longitude as "longitude",
                ps.date_disappear as "date_disappear"
            FROM
                db_pokestats.pokemon as p,
                db_pokestats.pokemon_spawnpoint ps
            WHERE
                    ps.latitude < {0}
                and ps.latitude > {1}
                and ps.longitude < {2}
                and ps.longitude > {3}
                and ps.date_disappear > now()
                and ps.cd_pokemon = p.id
        """.format(ne_latitude, sw_latitude, ne_longitude, sw_longitude)

        for row in session.execute(sqlalchemy.text(sql)):
            pokemons.append({
                "pokemon_id": row[0],
                "pokemon_name": row[1],
                "latitude": row[2],
                "longitude": row[3],
                "date_disappear": row[4]
            })

        return pokemons


    def _database_fetch_pokestops(self, session=None, ne_latitude=0, ne_longitude=0, sw_latitude=0, sw_longitude=0):
        pokestops = []

        sql = """
            SELECT
                p.name                  as "name",
                p.image_url             as "image",
                p.latitude	            as "latitude",
                p.longitude             as "longitude",
                p.date_lure_expiration  as "date_lure_expiration",
                p.date_change           as "date_change"
            FROM
                db_pokestats.pokestop as p
            WHERE
                    p.latitude < {0}
                and p.latitude > {1}
                and p.longitude < {2}
                and p.longitude > {3}
        """.format(ne_latitude, sw_latitude, ne_longitude, sw_longitude)

        for row in session.execute(sqlalchemy.text(sql)):
            pokestops.append({
                "name": row[0],
                "image": row[1],
                "latitude": row[2],
                "longitude": row[3],

                "date_lure_expiration": row[4],
                "date_change": row[5]
            })

        return pokestops

    def _database_fetch_gyms(self, session=None, ne_latitude=0, ne_longitude=0, sw_latitude=0, sw_longitude=0):
        gyms = []

        sql = """
            SELECT
                t.id as "team_id",
                t.name as "team_name",
                g.id as "gym_id",
                g.name as "gym_name",
                g.image_url  as "gym_image",
                g.prestige as "gym_prestige",
                g.latitude as "latitude",
                g.longitude as "longitude",
                g.date_change as "date_change"

            FROM
                db_pokestats.team as t,
                db_pokestats.gym as g
            WHERE
                    t.id = g.cd_team
                and g.latitude < {0}
                and g.latitude > {1}
                and g.longitude < {2}
                and g.longitude > {3}
        """.format(ne_latitude, sw_latitude, ne_longitude, sw_longitude)

        for row in session.execute(sqlalchemy.text(sql)):
            gyms .append({
                "team_id": row[0],
                "team_name": row[1],
                "gym_id": row[2],
                "gym_name": row[3],
                "gym_image": row[4],
                "gym_prestige": row[5],
                "latitude": row[6],
                "longitude": row[7],
                "date_change": row[8]
            })

        return gyms


    def _database_fetch_scanners(self, session=None, ne_latitude=0, ne_longitude=0, sw_latitude=0, sw_longitude=0):
        return []


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


    def json_put_user_geo(self):
        json_dict = {
            "saved": "true",
        }

        return jsonify(json_dict)

    def json_get_data(self):
        json_dict = {
            "scanned": [],
            "gyms": [],
            "pokestops": [],
            "pokemons": []
        }

        session = self._database_init()

        #try:
        if request.args.get('pokemon') == "true":
            json_dict['pokemons'] = self._database_fetch_pokemons(session=session, ne_latitude=request.args.get('ne_latitude'), ne_longitude=request.args.get('ne_longitude'), sw_latitude=request.args.get('sw_latitude'), sw_longitude=request.args.get('sw_longitude'))

        if request.args.get('pokestops') == "true":
            json_dict['pokestops'] = self._database_fetch_pokestops(session=session, ne_latitude=request.args.get('ne_latitude'), ne_longitude=request.args.get('ne_longitude'), sw_latitude=request.args.get('sw_latitude'), sw_longitude=request.args.get('sw_longitude'))

        if request.args.get('gyms') == "true":
            json_dict['gyms'] = self._database_fetch_gyms(session=session, ne_latitude=request.args.get('ne_latitude'), ne_longitude=request.args.get('ne_longitude'), sw_latitude=request.args.get('sw_latitude'), sw_longitude=request.args.get('sw_longitude'))

        if request.args.get('scanned') == "true":
            json_dict['scanned'] = self._database_fetch_scanners(session=session, ne_latitude=request.args.get('ne_latitude'), ne_longitude=request.args.get('ne_longitude'), sw_latitude=request.args.get('sw_latitude'), sw_longitude=request.args.get('sw_longitude'))
        #finally:
        self._database_close(session)

        return jsonify(json_dict)

    def json_put_data_geo(self):
        json_dict = {
            "saved": False,
            "latitude": self.conf_latitude,
            "longitude": self.conf_longitude
        }

        if request.args.get('latitude') and request.args.get('longitude'):
            json_dict['saved'] = True
            json_dict['latitude'] = request.args.get('latitude')
            json_dict['longitude'] = request.args.get('longitude')

        return jsonify(json_dict)

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
