# -*- coding: utf-8 -*-

import json
import time
import pprint
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

        log.info("GYM ownered by {0}, analyse".format(self.gym['owned_by_team']))

        action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

        response_index = 0

        while response_index < 5:
            response_dict = self.api.fort_details(fort_id=self.gym['id'])
            log.debug('Response dictionary: \r\n{}'.format(pprint.PrettyPrinter(indent=4).pformat(response_dict)))

            if response_dict and 'status_code' in response_dict:
                if response_dict['status_code'] is 1:
                    if 'responses' in response_dict:
                        if 'FORT_DETAILS' in response_dict['responses']:
                            if 'name' in response_dict['responses']['FORT_DETAILS']:
                                fort_name = response_dict['responses']['FORT_DETAILS']['name'].encode('utf8', 'replace')

                                log.info('[#] Now at GYM: ' + fort_name)

                                parse_fort_details(self.gym['id'], 0, response_dict['responses']['FORT_DETAILS'], self.session)

                                break
                            else:
                                log.warning("Получен неверный ответ, отсутствует имя GYM")
                                action_delay(self.ai.delay_action_min, self.ai.delay_action_max)
                else:
                    log.debug("Получен неверный статус: {0}".format(response_dict['status_code']))

                    if response_dict['status_code'] == 52:
                        action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

            response_index += 1

        action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

        response_index = 0

        while response_index < 5:
            response_dict = self.api.get_gym_details(gym_id=self.gym['id'],
                             player_latitude=f2i(self.position[0]),
                             player_longitude=f2i(self.position[1]))

            log.debug('Response dictionary: \r\n{}'.format(pprint.PrettyPrinter(indent=4).pformat(response_dict['responses'])))

            if response_dict and 'status_code' in response_dict:
                if response_dict['status_code'] is 1:
                    if 'responses' in response_dict:
                        if 'GET_GYM_DETAILS' in response_dict['responses']:
                            if 'gym_state' in response_dict['responses']['GET_GYM_DETAILS']:
                                if 'fort_data' in response_dict['responses']['GET_GYM_DETAILS']['gym_state']:
                                    self.gym = response_dict['responses']['GET_GYM_DETAILS']['gym_state']['fort_data']

                                    parse_gym(self.gym, self.session)

                                if 'memberships' in response_dict['responses']['GET_GYM_DETAILS']['gym_state']:
                                    clear_gym_membership(self.gym['id'], self.session)

                                    for membership in response_dict['responses']['GET_GYM_DETAILS']['gym_state']['memberships']:
                                        parse_gym_membership(membership, self.gym['id'], self.gym['owned_by_team'], self.session)

                                break
                            else:
                                log.warning("Получен неверный ответ, отсутствует состояние GYM")
                                action_delay(self.ai.delay_action_min, self.ai.delay_action_max)
                else:
                    log.debug("Получен неверный статус: {0}".format(response_dict['status_code']))

                    if response_dict['status_code'] == 52:
                        action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

            response_index += 1