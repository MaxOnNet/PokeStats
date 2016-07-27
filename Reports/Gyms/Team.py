#!/usr/bin/python
# -*- coding: utf-8 -*-
from math import floor
import datetime

from Reports.Report import Report
from flask.views import View


class Team(Report, View):
    methods = ['GET']

    sql_report = """
        SELECT
            t.`id` as "team_id",
            t.`name` as "team_name",
            count(g.id) as "gym_count"
        FROM
            db_pokestats.gym as g,
            db_pokestats.team as t
        where
            g.cd_team = t.id
        GROUP BY t.id
        ORDER BY count(g.id) DESC;
    """

    def __init__(self, config):
        Report.__init__(self, config, "report_gym_team.html")

    def dispatch_request(self):
        return self.render()


    def _prepare_data(self):
        result = self._database_execute(self.sql_report)

        for row in result:
            row_dict = {
                "team_id": row[0],
                "team_name": row[1],
                "gym_count": row[2]
            }
            self.data.append(row_dict)


