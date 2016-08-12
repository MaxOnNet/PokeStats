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
        self.conf_gmapkey = self.config_xml.get("map", "google", "key", "")


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

    def _database_fetch_pokemons(self, session=None, ne_latitude=0, ne_longitude=0, sw_latitude=0, sw_longitude=0, pokemon_time="now()", pokemon_ids=""):
        pokemons = []

        try:
            if int(pokemon_time) != -1:
                pokemon_time = "FROM_UNIXTIME({0})".format(str(pokemon_time))
            else:
                pokemon_time = "now()"
        except:
            pokemon_time = "now()"

        if pokemon_ids is not None:
            try:
                if int(pokemon_ids) != -1:
                    pokemon_ids = "and p.id in ({0})".format(pokemon_ids)
                else:
                    pokemon_ids = ""
            except:
                pokemon_ids = "and p.id in ({0})".format(pokemon_ids)
        else:
            pokemon_ids = ""

        sql = """
            SELECT
                p.id 	                as "id",
                p.name  	            as "name",
                ps.cd_encounter         as "encounter_id",
                ps.latitude	            as "latitude",
                ps.longitude            as "longitude",
                ps.date_disappear       as "date_disappear"
            FROM
                db_pokestats.pokemon as p,
                db_pokestats.pokemon_spawnpoint ps
            WHERE
                    ps.latitude < {0}
                and ps.latitude > {1}
                and ps.longitude < {2}
                and ps.longitude > {3}
                and ps.date_disappear > {4}
                and ps.cd_pokemon = p.id
                {5}

        """.format(ne_latitude, sw_latitude, ne_longitude, sw_longitude, pokemon_time, pokemon_ids)

        for row in session.execute(sqlalchemy.text(sql)):
            pokemons.append({
                "pokemon_id": row[0],
                "pokemon_name": row[1],
                "encounter_id": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "date_disappear": row[5]
            })

        return pokemons

    def _database_fetch_pokestops(self, session=None, ne_latitude=0, ne_longitude=0, sw_latitude=0, sw_longitude=0):
        pokestops = []

        sql = """
            SELECT
                p.id                    as "id",
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
                "id": row[0],
                "name": row[1],
                "image": row[2],
                "latitude": row[3],
                "longitude": row[4],

                "date_lure_expiration": row[5],
                "date_change": row[6]
            })

        return pokestops

    def _database_fetch_gyms(self, session=None, ne_latitude=0, ne_longitude=0, sw_latitude=0, sw_longitude=0):
        gyms = []

        sql = """
            SELECT
                t.id                as "team_id",
                t.name              as "team_name",
                g.id                as "gym_id",
                g.name              as "gym_name",
                g.image_url         as "gym_image",
                g.prestige          as "gym_prestige",
                g.latitude          as "latitude",
                g.longitude         as "longitude",
                g.date_change       as "date_change"

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
            gyms.append({
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
        scanners = []

        sql = """
            SELECT
                s.id 	                as "id",
                sl.latitude             as "latitude",
                sl.longitude            as "longitude",
                round(sl.distance*1000) as "distance",
                s.date_change           as "date_change"
            FROM
                db_pokestats.scanner as s,
                db_pokestats.scanner_location as sl,
                db_pokestats.scanner_account_statistic as sas
            WHERE
                    s.cd_location = sl.id
                and sas.cd_account = s.cd_account
                and sl.latitude < {0}
                and sl.latitude > {1}
                and sl.longitude < {2}
                and sl.longitude > {3}

        """.format(ne_latitude, sw_latitude, ne_longitude, sw_longitude)

        for row in session.execute(sqlalchemy.text(sql)):
            scanners.append({
                "id": row[0],
                "latitude": row[1],
                "longitude": row[2],
                "distance": row[3],
                "date_change": row[4]
            })

        return scanners


    def index(self):

        if request.args.get('latitude') and request.args.get('longitude'):
            pos_latitude = request.args.get('latitude')
            pos_longitude = request.args.get('longitude')
            pos_gps = 0
        else:
            pos_latitude = self.conf_latitude
            pos_longitude = self.conf_longitude
            pos_gps = 1

        if request.args.get('pokemon_ids'):
            pokemon_ids = request.args.get('pokemon_ids')
        else:
            pokemon_ids = -1

        if request.args.get('pokemon_time'):
            pokemon_time = request.args.get('pokemon_time')
        else:
            pokemon_time = -1

        return render_template('map.html',
                               lat=pos_latitude,
                               lng=pos_longitude,
                               gps=pos_gps,
                               pokemon_ids=pokemon_ids,
                               pokemon_time=pokemon_time,
                               gmaps_key=self.conf_gmapkey)


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

        if request.args.get('pokemon') == "true":
            json_dict['pokemons'] = self._database_fetch_pokemons(session=session, ne_latitude=request.args.get('ne_latitude'), ne_longitude=request.args.get('ne_longitude'), sw_latitude=request.args.get('sw_latitude'), sw_longitude=request.args.get('sw_longitude'), pokemon_time=request.args.get('pokemon_time'), pokemon_ids=request.args.get('pokemon_ids'))

        if request.args.get('pokestops') == "true":
            json_dict['pokestops'] = self._database_fetch_pokestops(session=session, ne_latitude=request.args.get('ne_latitude'), ne_longitude=request.args.get('ne_longitude'), sw_latitude=request.args.get('sw_latitude'), sw_longitude=request.args.get('sw_longitude'))

        if request.args.get('gyms') == "true":
            json_dict['gyms'] = self._database_fetch_gyms(session=session, ne_latitude=request.args.get('ne_latitude'), ne_longitude=request.args.get('ne_longitude'), sw_latitude=request.args.get('sw_latitude'), sw_longitude=request.args.get('sw_longitude'))

        if request.args.get('scanned') == "true":
            json_dict['scanned'] = self._database_fetch_scanners(session=session, ne_latitude=request.args.get('ne_latitude'), ne_longitude=request.args.get('ne_longitude'), sw_latitude=request.args.get('sw_latitude'), sw_longitude=request.args.get('sw_longitude'))

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

            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
