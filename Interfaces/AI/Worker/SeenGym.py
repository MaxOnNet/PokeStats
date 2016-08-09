# -*- coding: utf-8 -*-

import json
import time
import logging

from Interfaces.AI.Human import sleep, random_lat_long_delta, action_delay
from Interfaces.AI.Worker.Utils import distance, i2f, format_time

from Interfaces.pgoapi.utilities import f2i, h2f
from Interfaces.MySQL.Schema import parse_gym_membership, clear_gym_membership, parse_fort_details, parse_gym
log = logging.getLogger(__name__)


class SeenGym(object):
    def __init__(self, gym, ai):
        self.ai = ai
        self.api = ai.api
        self.session = ai.session
        self.position = ai.position
        self.stepper = ai.stepper

        self.gym = gym

        self.rest_time = 50


    def work(self):
        lat = self.gym['latitude']
        lng = self.gym['longitude']

        action_delay(self.ai.delay_action_min*2, self.ai.delay_action_max*2)

        log.info("GYM ownered by {0}, analyse".format(self.gym['owned_by_team']))
        response_dict = self.api.fort_details(fort_id=self.gym['id'])

        if 'responses' in response_dict \
                and'FORT_DETAILS' in response_dict['responses'] \
                and 'name' in response_dict['responses']['FORT_DETAILS']:
            fort_details = response_dict['responses']['FORT_DETAILS']
            fort_name = fort_details['name'].encode('utf8', 'replace')

            parse_fort_details(self.gym['id'], 0, fort_details, self.session)
        else:
            fort_name = 'Unknown'
        log.info('[#] Now at GYM: ' + fort_name)

        action_delay(self.ai.delay_action_min*2, self.ai.delay_action_max*2)

        response_dict = self.api.get_gym_details(gym_id=self.gym['id'],
                             player_latitude=f2i(self.position[0]),
                             player_longitude=f2i(self.position[1]))

        if 'responses' in response_dict \
                and'GET_GYM_DETAILS' in response_dict['responses'] \
                and 'gym_state' in response_dict['responses']['GET_GYM_DETAILS']\
                and 'fort_data' in response_dict['responses']['GET_GYM_DETAILS']['gym_state']:

                parse_gym(response_dict['responses']['GET_GYM_DETAILS']['gym_state']['fort_data'], self.session)
                self.gym = response_dict['responses']['GET_GYM_DETAILS']['gym_state']['fort_data']

        if 'responses' in response_dict \
                and'GET_GYM_DETAILS' in response_dict['responses'] \
                and 'gym_state' in response_dict['responses']['GET_GYM_DETAILS']\
                and 'memberships' in response_dict['responses']['GET_GYM_DETAILS']['gym_state']:

                clear_gym_membership(self.gym['id'], self.session)

                for membership in response_dict['responses']['GET_GYM_DETAILS']['gym_state']['memberships']:
                    parse_gym_membership(membership, self.gym['id'], self.gym['owned_by_team'], self.session)
