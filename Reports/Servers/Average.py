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
            s.state as "s_state",
            s.is_active as "s_active",
            sl.id as "sl_id",
            sl.address as "sl_address",
            sl.latitude as "sl_latitude",
            sl.longitude as "sl_longitude",
            s.is_active as "sl_fast",
            sa.id as "sa_id",
            sa.username as "sa_username",
            sa.service as "sa_service",
            sa.state as "sa_status",
            sa.is_active as "sa_active",
            (now() - ss.date_start) as "ss_await",
            ss.date_start as "ss_reload",
            ss.pokemons as "ss_pokemons",
            ss.gyms as "ss_gyms",
            ss.pokestops as "ss_pokestops",
            s.google_path as "s_google_path"
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
                "s_state": row[2],
                "s_active": row[3],
                "sl_id": row[4],
                "sl_address": row[5],
                "sl_latitude": row[6],
                "sl_longitude": row[7],
                "sl_fast": row[8],
                "sa_id": row[9],
                "sa_username": row[10],
                "sa_service": row[11],
                "sa_state": row[12],
                "sa_active": row[13],
                "ss_await": row[14],
                "ss_reload": row[15],
                "ss_pokemons": row[16],
                "ss_gyms": row[17],
                "ss_pokestops": row[18],
                "s_google_path": row[19]
            }

            self.data.append(row_dict)


