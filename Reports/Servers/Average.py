#!/usr/bin/python
# -*- coding: utf-8 -*-
from Reports.Report import Report
from flask.views import View


class Average(Report, View):
    methods = ['GET']

    sql_report = """
        SELECT
            s.id as "s_id",
            s.is_enable as "s_enable",
            sl.id as "sl_id",
            sl.address as "sl_address",
            sl.latitude as "sl_latitude",
            sl.longitude as "sl_longitude",
            sa.id as "sa_id",
            sa.username as "sa_username",
            sa.service as "sa_service",
            sa.status as "sa_status",
            (now() - ss.date_start) as "ss_await",
            ss.date_start as "ss_reload",
            ss.pokemons as "ss_pokemons",
            ss.gyms as "ss_gyms",
            ss.pokestops as "ss_pokestops"
        FROM
            db_pokestats.scanner as s,
            db_pokestats.scanner_account as sa,
            db_pokestats.scanner_location as sl,
            db_pokestats.scanner_statistic as ss
        WHERE
                s.cd_account = sa.id
            and s.cd_location = sl.id
            and s.id = ss.cd_scanner;
    """

    def __init__(self, config):
        Report.__init__(self, config, "report_server_average.html")

    def dispatch_request(self):
        return self.render()

    def _prepare_data(self):
        result = self._database_execute(self.sql_report)

        for row in result:
            row_dict = {
                "s_id": row[0],
                "s_enable": row[1],
                "sl_id": row[2],
                "sl_address": row[3],
                "sl_latitude": row[4],
                "sl_longitude": row[5],
                "sa_id": row[6],
                "sa_username": row[7],
                "sa_service": row[8],
                "sa_status": row[9],
                "ss_await": row[10],
                "ss_reload": row[11],
                "ss_pokemons": row[12],
                "ss_gyms": row[13],
                "ss_pokestops": row[14]
            }

            self.data.append(row_dict)


