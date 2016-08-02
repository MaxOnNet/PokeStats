#!/usr/bin/python
# -*- coding: utf-8 -*-
from Reports.Report import Report
from flask.views import View


class Account(Report, View):
    methods = ['GET']

    sql_report = """
        SELECT
            s.id 					as "s_id",
            s.is_enable  			as "s_enable",
            s.is_active 			as "s_active",

            sa.username 			as "sa_login",
            sac.username			as "sa_name",
            sac.level				as "sa_level",
            sac.experience_to_level as "sa_exp2lev",

            sac.stardust			as "sa_stardust",
            sac.pokecoins 			as "sa_coins",

            sac.bag_items 			as "sa_bag_items",
            sac.bag_pokemons 		as "sa_bag_pokemons",

            sac.visited_pokestops 	as "sa_seen_pokestops",
            sac.catched_pokemons 	as "sa_seen_pokemons",

            sac.item_ball_poke 		as "sa_ball_poke",
            sac.item_ball_great 	as "sa_ball_great",
            sac.item_ball_ultra 	as "sa_ball_ultra",
            sac.item_ball_master 	as "sa_ball_master",

            sac.item_potion 		as "sa_potion_normal",
            sac.item_potion_super 	as "sa_potion_super",
            sac.item_potion_hyper 	as "sa_potion_huper",
            sac.item_potion_master	as "sa_potion_max",

            sac.item_revive 		as "sa_revive_normal",
            sac.item_revive_master 	as "sa_revive_master",

            sac.item_berry_razz 	as "sa_berry_razz",
            sac.item_berry_bluk 	as "sa_berry_bluk",
            sac.item_berry_nanab 	as "sa_berry_nanab",
            sac.item_berry_wepar	as "sa_berry_wepar",
            sac.item_berry_pinap	as "sa_berry_pinap"
         FROM
            db_pokestats.scanner s,
            db_pokestats.scanner_account sa,
            db_pokestats.scanner_account_statistic sac
        WHERE
                s.cd_account = sa.id
            and s.cd_account = sac.cd_account
        ORDER BY sac.level DESC, sac.experience_to_level ASC;
    """

    def __init__(self, config):
        Report.__init__(self, config, "report_server_account.html")

    def dispatch_request(self):
        return self.render()

    def _prepare_data(self):
        result = self._database_execute(self.sql_report)

        for row in result:
            row_dict = {
                "s_id": row[0],
                "s_enable": row[1],
                "s_active": row[2],

                "sa_login": row[3],
                "sa_name": row[4],
                "sa_level": row[5],
                "sa_exp2lev": row[6],

                "sa_stardust": row[7],
                "sa_coins": row[8],

                "sa_bag_items": row[9],
                "sa_bag_pokemons": row[10],

                "sa_seen_pokestops": row[11],
                "sa_seen_pokemons": row[12],

                "sa_ball_poke": row[13],
                "sa_ball_great": row[14],
                "sa_ball_ultra": row[15],
                "sa_ball_master": row[16],

                "sa_potion_normal": row[17],
                "sa_potion_super": row[18],
                "sa_potion_huper": row[19],
                "sa_potion_max": row[20],

                "sa_revive_normal": row[21],
                "sa_revive_master": row[22],

                "sa_berry_razz": row[23],
                "sa_berry_bluk": row[24],
                "sa_berry_nanab": row[25],
                "sa_berry_wepar": row[26],
                "sa_berry_pinap": row[27]
            }

            self.data.append(row_dict)


