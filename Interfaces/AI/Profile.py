# -*- coding: utf-8 -*-

import datetime
import os
import json
import time
import pprint
import logging

log = logging.getLogger(__name__)


class Profile:
    def __init__(self, thread):
        self.scanner = thread.scanner
        self.session = thread.session

        self.api = thread.api

        self.inventory = list()


    def update(self):
        log.info("Обновляем данные профиля.")

        self.api.get_player()
        response_dict = self.api.call()

        if response_dict and 'status_code' in response_dict:
            if response_dict['status_code'] is 1:
                if 'responses' in response_dict:
                    if 'GET_PLAYER' in response_dict['responses']:
                        if 'status' in response_dict['responses']['GET_PLAYER']:
                            if response_dict['responses']['GET_PLAYER']['status'] is 1:
                                if 'player_data' in response_dict['responses']['GET_PLAYER']:
                                    try:
                                        profile_res = response_dict['responses']['GET_PLAYER']['player_data']

                                        self.scanner.account.statistic.username = profile_res['username']
                                        self.scanner.account.statistic.date_start = datetime.datetime.fromtimestamp(profile_res['creation_timestamp_ms'] / 1e3)

                                        if 'amount' in profile_res['currencies'][0]:
                                            self.scanner.account.statistic.pokecoins = profile_res['currencies'][0]['amount']
                                        if 'amount' in profile_res['currencies'][1]:
                                            self.scanner.account.statistic.stardust = profile_res['currencies'][1]['amount']

                                    except Exception as e:
                                        log.error("Ошибка при обновлении провиля:{0}".fotmat(e))

                                    self.session.commit()
                            else:
                                log.warning("Получен неверный статус: {0}".format(response_dict['responses']['GET_PLAYER']['status']))
                    else:
                        log.warning("Получен неверный статус: {0}".format(response_dict['status_code']))



