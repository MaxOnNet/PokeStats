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
            tm.`id`         as "team_id",
            tm.`name`       as "team_name",
            g.count     as "gym_count",
            t.count    as "trainer_count"
        FROM
            db_pokestats.team      as tm
            LEFT JOIN
            (
				SELECT
					tm.`id`         as "team_id",
                    count(g.id)     as "count"
				FROM
					db_pokestats.team      as tm,
                    db_pokestats.gym		as g
				WHERE
					g.cd_team = tm.id
				GROUP BY tm.`id` ) g on (g.team_id = tm.id)
            LEFT JOIN
            (
				SELECT
					tm.`id`         as "team_id",
                    count(t.id)     as "count"
				FROM
					db_pokestats.team      as tm,
                    db_pokestats.trainer		as t
				WHERE
					t.cd_team = tm.id
				GROUP BY tm.`id` ) t on (t.team_id = tm.id)
        WHERE
                tm.id = g.team_id
            and tm.id = t.team_id
        GROUP BY tm.id
        ORDER BY g.count DESC;
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
                "gym_count": row[2],
                "trainer_count": row[3]
            }
            self.data.append(row_dict)


