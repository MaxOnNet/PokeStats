#!/usr/bin/python
# -*- coding: utf-8 -*-
from math import floor
import datetime

from Reports.Report import Report
from flask import request
from flask.views import View


class Membership(Report, View):
    methods = ['GET']

    sql_report = """
        SELECT
            tm.id 				as "team_id",
            tm.name 			as "team_name",
            tr.id 				as "trainer_id",
            tr.name				as "trainer_name",
            tr.level 			as "trainer_level",
            p.id				as "pokemon_id",
            p.name				as "pokemon_name",
            gm.pokemon_nickname as "pokemon_nickname",
            gm.pokemon_cp 		as "pokemon_cp"

        FROM

            db_pokestats.gym g
            LEFT JOIN db_pokestats.gym_membership gm on (g.id = gm.cd_gym)
            LEFT JOIN db_pokestats.trainer tr on (gm.cd_trainer = tr.id)
            LEFT JOIN db_pokestats.pokemon p on (gm.cd_pokemon = p.id)
            LEFT JOIN db_pokestats.team tm on (gm.cd_team = tm.id)
        WHERE
            g.id = "{0}"
        ORDER BY gm.pokemon_cp DESC
    """

    def __init__(self, config):
        Report.__init__(self, config, "report_gym_membership.html")


    def dispatch_request(self):
        return self.render()


    def _prepare_data(self):
        gym_id = request.args.get("gym_id")
        result = self._database_execute(self.sql_report.format(gym_id))

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
                "pokemon_cp": row[8]
            }
            self.data.append(row_dict)


