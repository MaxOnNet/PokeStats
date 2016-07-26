#!/usr/bin/python
# -*- coding: utf-8 -*-
from Reports.Report import Report
from flask.views import View


class Top(Report, View):
    methods = ['GET']

    sql_report = """
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
            (now() - g.date_change) as "srv_await",
            g.name as "gym_name",
            g.address as "gym_address",
            g.description as "gym_description"

        FROM
            db_pokestats.gym as g,
            db_pokestats.team as t,
            db_pokestats.pokemon as p
        WHERE
                g.cd_team = t.id
            and g.cd_team != 0
            and g.cd_guard_pokemon = p.id

        ORDER BY
            g.prestige DESC
        LIMIT 0,50;
    """

    def __init__(self, config):
        Report.__init__(self, config, "report_gym_top.html")

    def dispatch_request(self):
        return self.render()

    def _prepare_data(self):
        result = self._database_execute(self.sql_report)

        for row in result:
            row_dict = {
                "gym_id": row[0],
                "gym_prestige": row[1],
                "gym_longitude": row[2],
                "gym_latitude": row[3],
                "gym_modified": row[4],
                "gym_viewed": row[5],
                "team_id": row[6],
                "team_name": row[7],
                "pokemon_guard_id": row[8],
                "pokemon_guard_name": row[9],
                "gym_await": row[10],
                "gym_name": row[11],
                "gym_address": row[12],
                "gym_description": row[13]
            }
            self.data.append(row_dict)


