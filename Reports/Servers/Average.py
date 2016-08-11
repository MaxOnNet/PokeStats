#!/usr/bin/python
# -*- coding: utf-8 -*-
from Reports.Report import Report
from flask.views import View


class Average(Report, View):
    methods = ['GET']

    sql_report_servers = """
        SELECT
            ss.id 	            as "server_id",
            ss.is_enable	    as "server_enable",
            ss.name	            as "server_name",
            ss.description      as "server_description",
            ss.ip               as "server_ip",
            ss.hostname         as "server_hostname",
            ss.address          as "server_address"
        FROM
            db_pokestats.scanner_server as ss
        ORDER BY
            ss.id ASC;
    """

    sql_report = """
        SELECT
            s.id 			as "s_id",
            s.is_enable 	as "s_enable",
            s.is_active 	as "s_active",
            s.state 		as "s_state",
			s.latitude		as "s_latitude",
            s.longitude		as "s_longitude",
            s.google_path 	as "s_google_path",

            sl.id 			as "sl_id",
            sl.address 		as "sl_address",
            sl.latitude 	as "sl_latitude",
            sl.longitude 	as "sl_longitude",
			sl.distance		as "sl_distance",

            sa.id 			as "sa_id",
            sa.username 	as "sa_username",
            sa.service 		as "sa_service",
            sa.state 		as "sa_status",
            sa.is_active 	as "sa_active",

            (now() - ss.date_start) as "ss_await",
            ss.date_start 			as "ss_reload",
            ss.pokemons 			as "ss_pokemons",
            ss.gyms 				as "ss_gyms",
            ss.pokestops 			as "ss_pokestops",

            sm.stepper		as "sm_stepper",
            sm.step			as "sm_step",
            sm.walk			as "sm_walk",
            sm.is_catch		as "sm_catch",
            sm.is_farm		as "sm_farm",
            sm.is_lookup	as "sm_lookup",
            sm.is_search	as "sm_search",

            s.is_throttled as "s_throttled",
            s.is_warning as "s_warning"

        FROM
            db_pokestats.scanner as s,
            db_pokestats.scanner_account as sa,
            db_pokestats.scanner_location as sl,
            db_pokestats.scanner_statistic as ss,
            db_pokestats.scanner_mode as sm
        WHERE
                s.cd_account = sa.id
            and s.cd_location = sl.id
            and s.id = ss.cd_scanner
            and s.cd_mode = sm.id
            and s.cd_server = {};
    """

    def __init__(self, config):
        Report.__init__(self, config, "report_server_average.html")

    def dispatch_request(self):
        return self.render()

    def _prepare_data(self):
        result_servers = self._database_execute(self.sql_report_servers)

        for row_server in result_servers:
            row_data = []
            row_dict = {}

            result = self._database_execute(self.sql_report.format(int(row_server[0])))

            for row in result:
                row_dict = {
                    "s_id": row[0],
                    "s_enable": row[1],
                    "s_active": row[2],
                    "s_state": row[3],
                    "s_latitude": row[4],
                    "s_longitude": row[5],
                    "s_google_path": row[6],

                    "sl_id": row[7],
                    "sl_address": row[8],
                    "sl_latitude": row[9],
                    "sl_longitude": row[10],
                    "sl_distance": row[11],

                    "sa_id": row[12],
                    "sa_username": row[13],
                    "sa_service": row[14],
                    "sa_state": row[15],
                    "sa_active": row[16],

                    "ss_await": row[17],
                    "ss_reload": row[18],
                    "ss_pokemons": row[19],
                    "ss_gyms": row[20],
                    "ss_pokestops": row[21],

                    "sm_stepper": row[22],
                    "sm_step": row[23],
                    "sm_walk": row[24],
                    "sm_catch": row[25],
                    "sm_farm": row[26],
                    "sm_lookup": row[27],
                    "sm_search": row[28],
                    "s_throttled": row[29],
                    "s_warning": row[30]
                }

                row_data.append(row_dict)

            row_dict = {
                "server_id": row_server[0],
                "server_enable": row_server[1],
                "server_name": row_server[2],
                "server_description": row_server[3],
                "server_ip": row_server[4],
                "server_hostname": row_server[5],
                "server_address": row_server[6],
                "server_data": row_data
            }

            self.data.append(row_dict)
