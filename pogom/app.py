#!/usr/bin/python
# -*- coding: utf-8 -*-

import calendar
from flask import Flask, jsonify, render_template, request
from flask.json import JSONEncoder


from datetime import datetime

from Interfaces.Config import Config
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import PokemonSpawnpoint, Gym, Pokestop, Pokemon, Scanner, ScannerStatistic, ScannerLocation
import sqlalchemy
from sqlalchemy import text as sql_text
from . import config


class Pogom(Flask):
    sql_report_gym_top = """
            SELECT
            g.id as "gym_id",
            g.prestige as "gym_prestige",
            g.longitude as "gym_longitude",
            g.latitude as "gym_latitude",
            g.date_modified as "gym_modified",
            g.date_change as "srv_viewed",
            g.cd_team as "team_id",
            t.name as "team_name",
            g.cd_guard_pokemon as "pokemon_cd",
            p.name	as "pokemon_name",
            (now() - g.date_change) as "srv_await"

        FROM
            db_pokestats.gym as g,
            db_pokestats.team as t,
            db_pokestats.pokemon as p
        Where
                g.cd_team = t.id
            and g.cd_team != 0
            and g.cd_guard_pokemon = p.id

        ORDER BY
            g.prestige DESC
        LIMIT 0,50;
	"""

    sql_report_pokemon_average = """
        SELECT
            p.id,
            p.name,
            COALESCE(ps_now.pokemon_count,"") as "count_now",
            COALESCE(ps_hour.pokemon_count,"") as "count_hour",
            COALESCE(ps_day.pokemon_count,"") as "count_day",
            COALESCE(ps_all.pokemon_count,"") as "count_all"
        FROM
            db_pokestats.pokemon p
            LEFT JOIN
            (
                SELECT
                    ps.cd_pokemon as cd_pokemon,
                    count(ps.id) as pokemon_count
                FROM
                    db_pokestats.pokemon_spawnpoint ps
                WHERE
                    ps.date_disappear > now()
                GROUP BY
                    ps.cd_pokemon) ps_now on (p.id = ps_now.cd_pokemon)
            LEFT JOIN
            (
                SELECT
                    ps.cd_pokemon as cd_pokemon,
                    count(ps.id) as pokemon_count
                FROM
                    db_pokestats.pokemon_spawnpoint ps
                WHERE
                    DATE_ADD(ps.date_disappear, INTERVAL 1 HOUR) > now()
                GROUP BY
                    ps.cd_pokemon) ps_hour on (p.id = ps_hour.cd_pokemon)
            LEFT JOIN
            (
                SELECT
                    ps.cd_pokemon as cd_pokemon,
                    count(ps.id) as pokemon_count
                FROM
                    db_pokestats.pokemon_spawnpoint ps
                WHERE
                    DATE_ADD(ps.date_disappear, INTERVAL 1 DAY) > now()
                GROUP BY
                    ps.cd_pokemon) ps_day on p.id = (ps_day.cd_pokemon)
            LEFT JOIN
            (
                SELECT
                    ps.cd_pokemon as cd_pokemon,
                    count(ps.id) as pokemon_count
                FROM
                    db_pokestats.pokemon_spawnpoint ps
                GROUP BY
                    ps.cd_pokemon) ps_all on (p.id = ps_all.cd_pokemon)
        where
            p.id < 150
        GROUP BY p.id
        ORDER BY p.id;
        """

    sql_report_pokemon_now = """
        SELECT
            p.id as "pokemon_id",
            p.name as "pokemon_name",
            p.group as "pokemon_group",
            p.evolution as "pokemon_evolution",
            count(ps.cd_pokemon) as "respawn_count",
            min((ps.date_disappear - now())) as "respawn_seconds_min",
            max((ps.date_disappear - now())) as "respawn_seconds_max",
            ps.latitude as "respawn_latitude",
	        ps.longitude as "respawn_longitude"
        FROM
            db_pokestats.pokemon_spawnpoint ps,
            db_pokestats.pokemon p
        WHERE
                ps.cd_pokemon = p.id
            and ps.date_disappear > now()
        GROUP BY
            p.name, p.id
        ORDER BY
            p.id;

        """
    def __init__(self, import_name, **kwargs):
        super(Pogom, self).__init__(import_name, **kwargs)
        self.json_encoder = CustomJSONEncoder
        self.route("/", methods=['GET'])(self.fullmap)
        self.route("/report/gym/top", methods=['GET'])(self.report_gym_top)
        self.route("/report/pokemon/average", methods=['GET'])(self.report_pokemon_average)
        self.route("/report/pokemon/now", methods=['GET'])(self.report_pokemon_now)

        self.route("/raw_data", methods=['GET'])(self.raw_data)
        self.route("/next_loc", methods=['POST'])(self.next_loc)
        self.config_xml = Config()



    def _database_init(self):
        self.session_maker = init(self.config_xml)
        self.session_mysql = self.session_maker()

    def _database_close(self):
        self.session_mysql.flush()
        self.session_mysql.expunge_all()
        self.session_mysql.close()

    def report_gym_top(self):
        self._database_init()
        sql = sql_text(self.sql_report_gym_top)
        result = self.session_mysql.execute(sql)
        table = []
        self._database_close()
        for row in result:
            row_dict = {
                "gym_id" : row[0],
                "gym_prestige" : row[1],
                "gym_longitude" : row[2],
                "gym_latitude" : row[3],
                "gym_modified" : row[4],
                "gym_viewed" : row[5],
                "team_id" : row[6],
                "team_name" : row[7],
                "pokemon_guard_id" : row[8],
                "pokemon_guard_name" : row[9],
                "gym_await" : row[10]
            }
            table.append(row_dict)

        return render_template('report_gym_top.html', table=table)


    def report_pokemon_average(self):
        self._database_init()
        sql = sql_text(self.sql_report_pokemon_average)
        result = self.session_mysql.execute(sql)
        table = []
        self._database_close()
        for row in result:
            row_dict = {
                "pokemon_id" : row[0],
                "pokemon_name" : row[1],
                "count_now" : row[2],
                "count_hour" : row[3],
                "count_day" : row[4],
                "count_all" : row[5]
            }
            table.append(row_dict)

        return render_template('report_pokemon_average.html', table=table)


    def report_pokemon_now(self):
        self._database_init()
        sql = sql_text(self.sql_report_pokemon_now)
        result = self.session_mysql.execute(sql)
        table = []
        self._database_close()
        for row in result:
            row_dict = {
                "pokemon_id" : row[0],
                "pokemon_name" : row[1],
                "pokemon_group" : row[2],
                "pokemon_evolution" : row[3],
                "respawn_count" : row[4],
                "respawn_seconds_min" : row[5],
                "respawn_seconds_max" : row[6],
                "respawn_latitude": row[7],
                "respawn_longitude": row[8]
            }
            table.append(row_dict)

        return render_template('report_pokemon_now.html', table=table)


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
