#!/usr/bin/python
# -*- coding: utf-8 -*-
from Interfaces.Pokedex import Pokedex
from Reports.Report import Report
from flask.views import View

pokedex = Pokedex()


class Average(Report, View):
    methods = ['GET']

    sql_report = """
        SELECT
            p.id as "pokemon_id",
            p.name as "pokemon_name",
            p.group as "pokemon_group",
            p.evolution as "pokemon_evolution",
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
        WHERE
            p.id < 150
        GROUP BY p.id
        ORDER BY p.id;
    """

    def __init__(self, config):
        Report.__init__(self, config, "report_pokemon_average.html")

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
                "count_now": row[4],
                "count_hour": row[5],
                "count_day": row[6],
                "count_all": row[7],
                "pokemon_rarity": pokedex.get_rarity_by_id(row[0]),
                "pokemon_rarity_name": pokedex.get_rarity_name_by_id(pokedex.get_rarity_by_id(row[0])),
                "pokemon_evolve": pokedex.get_evolve_by_id(row[0])
            }
            self.data.append(row_dict)


