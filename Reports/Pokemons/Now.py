#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime

from flask.views import View

from Interfaces.AI.Pokedex import Pokedex
from Reports.Report import Report

pokedex = Pokedex()

class Now(Report, View):
    methods = ['GET']

    sql_report = """
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

    def __init__(self, config):
        Report.__init__(self, config, "report_pokemon_now.html")

    def dispatch_request(self):
        return self.render()

    def _prepare_data(self):
        result = self._database_execute(self.sql_report)

        for row in result:
            row_dict = {
                "pokemon_id": row[0],
                "pokemon_name": row[1],
                "pokemon_group": row[2],
                "pokemon_evolution": row[3],
                "respawn_count": row[4],
                "respawn_seconds_min": self.format_timedelta(datetime.timedelta(seconds=row[5]), "{minutes2}m{seconds2}s"),
                "respawn_seconds_max": self.format_timedelta(datetime.timedelta(seconds=row[6]), "{minutes2}m{seconds2}s"),
                "respawn_latitude": row[7],
                "respawn_longitude": row[8],
                "pokemon_rarity": pokedex.get_rarity_by_id(row[0]),
                "pokemon_rarity_name": pokedex.get_rarity_name_by_id(pokedex.get_rarity_by_id(row[0])),
                "pokemon_evolve": pokedex.get_evolve_by_id(row[0])
            }

            self.data.append(row_dict)


