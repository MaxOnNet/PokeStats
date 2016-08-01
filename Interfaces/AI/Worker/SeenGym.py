# -*- coding: utf-8 -*-

import json
import time
import logging

from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Worker.Utils import distance, i2f, format_time

from Interfaces.pgoapi.utilities import f2i, h2f
from Interfaces.MySQL.Schema import parse_gym_membership, clear_gym_membership, parse_fort_details
log = logging.getLogger(__name__)


class SeenGym(object):
    def __init__(self, gym, ai):
        self.gym = gym
        self.api = ai.api
        self.ai = ai
        self.position = ai.position

        self.rest_time = 50
        self.stepper = ai.stepper

    def work(self):
        lat = self.gym['latitude']
        lng = self.gym['longitude']

        if self.gym['owned_by_team'] !=0:
            log.info("GYM ownered by {0}, analyse".format(self.gym['owned_by_team']))
            self.api.fort_details(fort_id=self.gym['id'], latitude=lat, longitude=lng)
            response_dict = self.api.call()
            if 'responses' in response_dict \
                    and'FORT_DETAILS' in response_dict['responses'] \
                    and 'name' in response_dict['responses']['FORT_DETAILS']:
                fort_details = response_dict['responses']['FORT_DETAILS']
                fort_name = fort_details['name'].encode('utf8', 'replace')

                parse_fort_details(self.gym['id'], 0, fort_details, self.ai.scanner_thread.session_mysql)
            else:
                fort_name = 'Unknown'
            log.info('[#] Now at GYM: ' + fort_name)
            sleep(1)

            self.api.get_gym_details(gym_id=self.gym['id'],
                                 gym_latitude=lat,
                                 gym_longitude=lng,
                                 player_latitude=f2i(self.position[0]),
                                 player_longitude=f2i(self.position[1]))
            response_dict = self.api.call()
            if 'responses' in response_dict \
                    and'GET_GYM_DETAILS' in response_dict['responses'] \
                    and 'gym_state' in response_dict['responses']['GET_GYM_DETAILS']\
                    and 'memberships' in response_dict['responses']['GET_GYM_DETAILS']['gym_state']:

                    clear_gym_membership(self.gym['id'], self.ai.scanner_thread.session_mysql)

                    for membership in response_dict['responses']['GET_GYM_DETAILS']['gym_state']['memberships']:
                        parse_gym_membership(membership, self.gym['id'], self.gym['owned_by_team'], self.ai.scanner_thread.session_mysql)
        else:
            parse_gym_membership(None, self.gym['id'], 0, self.ai.scanner_thread.session_mysql)
            log.info("GYM Unused, skipped")
