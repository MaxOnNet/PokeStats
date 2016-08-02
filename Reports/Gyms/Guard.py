#!/usr/bin/python
# -*- coding: utf-8 -*-
from math import floor
import datetime

from Reports.Report import Report
from flask.views import View


class Guard(Report, View):
    methods = ['GET']

    sql_report = """
        SELECT
            tm.id as "team_id",
            tm.name as "team_name",
            tr.id as "trainer_id",
            tr.name as "trainer_name",
            tr.level as "trainer_level",
            p.id as "pokemon_id",
            p.name as "pokemon_name",
            gm.pokemon_nickname as "pokemon_nickname",
            gm.pokemon_cp as "pokemon_cp",
            g.id as "gym_id",
            g.name as "gym_name"
        FROM
            db_pokestats.gym_membership gm,
            db_pokestats.team tm,
            db_pokestats.pokemon p,
            db_pokestats.gym g,
            db_pokestats.trainer tr
        WHERE
                gm.cd_team = tm.id
            and gm.cd_gym = g.id
            and gm.cd_trainer = tr.id
            and gm.cd_pokemon = p.id

        ORDER BY gm.pokemon_cp DESC
        LIMIT 0,100;
    """

    def __init__(self, config):
        Report.__init__(self, config, "report_gym_guard.html")

    def dispatch_request(self):
        return self.render()


    def _prepare_data(self):
        result = self._database_execute(self.sql_report)

        for row in result:
            row_dict = {
                "team_id": row[0],
                "team_name": row[1],
                "trainer_id": row[2],
                "trainer_name": row[3],
                "trainer_level": row[4],
                "pokemon_id": row[5],
                "pokemon_name": row[6],
                "pokemon_nickname": row[7],
                "pokemon_cp": row[8],
                "gym_id": row[9],
                "gym_name": row[10]
            }
            self.data.append(row_dict)


