#!/usr/bin/python
# -*- coding: utf-8 -*-
from math import floor
import datetime
import json
from Reports.Report import Report
from flask.views import View


class Top(Report, View):
    methods = ['GET']

    sql_report = '''
        SELECT
            tm.id 		as "team_id",
            tm.name 	as "team_name",
            tr.id		as "trainer_id",
            tr.name		as "trainer_name",
            tr.level	as "trainer_level",
            count(gm.id)as "gym_count",
            COALESCE(concat("[",group_concat(concat('["',gm.cd_gym, '", "', REPLACE(g.name,'"', '') ,'"]') separator ","),"]"),"[]") as "gym_json"
        FROM
			db_pokestats.team tm,

            db_pokestats.trainer tr
            LEFT JOIN (db_pokestats.gym_membership gm) on (tr.id = gm.cd_trainer)
            LEFT JOIN (db_pokestats.gym g) on (g.id = gm.cd_gym)
		WHERE
			tm.id = tr.cd_team
        Group by tm.name, tr.name
        order by tr.level DESC, tr.name ASC, gm.id ASC
        LIMIT 0,100;
    '''

    def __init__(self, config):
        Report.__init__(self, config, "report_trainer_top.html")

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
                "gym_count": row[5],
                "gym_json": json.loads(row[6])

            }
            self.data.append(row_dict)


