# -*- coding: utf-8 -*-

import json
import time
import logging

from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Worker.Utils import distance, i2f, format_time
from Interfaces.MySQL.Schema import parse_fort_details
from Interfaces.pgoapi.utilities import f2i, h2f

log = logging.getLogger(__name__)


class SeenPokestop(object):
    def __init__(self, pokestop, ai):
        self.ai = ai
        self.api = ai.api
        self.session = ai.session
        self.position = ai.position
        self.stepper = ai.stepper

        self.pokestop = pokestop
        self.rest_time = 50


    def work(self):
        lat = self.pokestop['latitude']
        lng = self.pokestop['longitude']

        self.api.fort_details(fort_id=self.pokestop['id'], latitude=lat, longitude=lng)
        response_dict = self.api.call()
        if 'responses' in response_dict \
                and'FORT_DETAILS' in response_dict['responses'] \
                and 'name' in response_dict['responses']['FORT_DETAILS']:
            fort_details = response_dict['responses']['FORT_DETAILS']
            fort_name = fort_details['name'].encode('utf8', 'replace')

            parse_fort_details(self.pokestop['id'], 1, fort_details, self.session)
        else:
            fort_name = 'Unknown'
        log.info('[#] Now at Pokestop: ' + fort_name + ' - Spinning...')
        sleep(1)
        self.api.fort_search(fort_id=self.pokestop['id'],
                             fort_latitude=lat,
                             fort_longitude=lng,
                             player_latitude=f2i(self.position[0]),
                             player_longitude=f2i(self.position[1]))
        response_dict = self.api.call()
        if 'responses' in response_dict and \
                'FORT_SEARCH' in response_dict['responses']:

            spin_details = response_dict['responses']['FORT_SEARCH']
            if spin_details['result'] == 1:
                log.info("[+] Loot: ")
                experience_awarded = spin_details.get('experience_awarded', False)
                if experience_awarded:
                    log.info("[+] " + str(experience_awarded) + " xp")

                items_awarded = spin_details.get('items_awarded', False)

                if items_awarded:
                    tmp_count_items = {}
                    for item in items_awarded:
                        item_id = item['item_id']
                        if not item_id in tmp_count_items:
                            tmp_count_items[item_id] = item['item_count']
                        else:
                            tmp_count_items[item_id] += item['item_count']

                    for item_id, item_count in tmp_count_items.iteritems():
                        log.info("[+] Loot: {0} count {1}".format(item_id, item_count))
                else:
                    log.info("[#] Nothing found.")

                pokestop_cooldown = spin_details.get('cooldown_complete_timestamp_ms')
                if pokestop_cooldown:
                    seconds_since_epoch = time.time()
                    log.info('[#] PokeStop on cooldown. Time left: ' + str(
                        format_time((pokestop_cooldown / 1000) - seconds_since_epoch)))

                if not items_awarded and not experience_awarded and not pokestop_cooldown:
                    log.warning(
                        'Stopped at Pokestop and did not find experience, items '
                        'or information about the stop cooldown. You are '
                        'probably softbanned. Try to play on your phone, '
                        'if pokemons always ran away and you find nothing in '
                        'PokeStops you are indeed softbanned. Please try again '
                        'in a few hours.')
            elif spin_details['result'] == 2:
                log.info("[#] Pokestop out of range")
            elif spin_details['result'] == 3:
                pokestop_cooldown = spin_details.get(
                    'cooldown_complete_timestamp_ms')
                if pokestop_cooldown:
                    seconds_since_epoch = time.time()
                    log.info('[#] PokeStop on cooldown. Time left: ' + str(
                        format_time((pokestop_cooldown / 1000) -
                                    seconds_since_epoch)))
            elif spin_details['result'] == 4:
                log.info("[#] Inventory is full, switching to catch mode...")
                #self.config.mode = 'poke'

            if 'chain_hack_sequence_number' in response_dict['responses'][
                    'FORT_SEARCH']:
                time.sleep(2)
                return response_dict['responses']['FORT_SEARCH'][
                    'chain_hack_sequence_number']
            else:
                log.info('[#] may search too often, lets have a rest')
                return 11
        sleep(8)
        return 0

    @staticmethod
    def closest_fort(current_lat, current_long, forts):
        print 'x'
