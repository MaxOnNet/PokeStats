# -*- coding: utf-8 -*-

import datetime
import json
import logging
import random
import re
import sys

#from Interfaces.AI.Worker import PokemonCatch, EvolveAll, MoveToPokestop, , InitialTransfer
from Interfaces.AI.Worker import MoveToPokestop, SeenPokestop
from Interfaces.AI.Worker.Utils import distance
from Interfaces.AI.Stepper.Normal import Normal as Stepper

from Interfaces.MySQL.Schema import parse_pokemon_cell, parse_gym, parse_pokestop
from Interfaces.Geolocation import Geolocation

from Interfaces import Logger
from Inventory import Item


class AI(object):
    def __init__(self, scanner_thread):
        self.scanner_thread = scanner_thread
        self.api = scanner_thread.api
        self.config = scanner_thread.config
        self.scanner = scanner_thread.scanner
        self.stepper = Stepper(self)

        self.position = [0, 0, 0]

    def take_step(self):
       # worker = InitialTransfer(self)
       # worker.work()

        self.update_inventory()
        self.stepper.take_step()

    def work_on_cell(self, cell, position, include_fort_on_path):
        self.position = position

        report = {
            "pokemons": 0,
            "pokestops": 0,
            "gyms": 0
        }

        if 'catchable_pokemons' in cell and len(cell['catchable_pokemons']) > 0:
            cell['catchable_pokemons'].sort(key=lambda x: distance(position[0], position[1], x['latitude'], x['longitude']))

            #for pokemon in cell['catchable_pokemons']:
            #    if self.catch_pokemon(pokemon) == PokemonCatch.NO_POKEBALLS:
            #        break

        if 'wild_pokemons' in cell and len(cell['wild_pokemons']) > 0:
            cell['wild_pokemons'].sort(key=lambda x: distance(position[0], position[1], x['latitude'], x['longitude']))

            report['pokemons'] += parse_pokemon_cell(cell, self.scanner_thread.session_mysql)

            #for pokemon in cell['wild_pokemons']:
            #    if self.catch_pokemon(pokemon) == PokemonCatch.NO_POKEBALLS:
            #        break

        if include_fort_on_path:
            if 'forts' in cell:
                # Only include those with a lat/long
                pokestops = [pokestop for pokestop in cell['forts'] if 'latitude' in pokestop and 'type' in pokestop]
                gyms = [gym for gym in cell['forts'] if 'gym_points' in gym]

                for pokestop in pokestops:
                    report['pokestops'] += parse_pokestop(pokestop, self.scanner_thread.session_mysql)

                for gym in gyms:
                    report['gyms'] += parse_gym(gym, self.scanner_thread.session_mysql)

                # Sort all by distance from current pos- eventually this should
                # build graph & A* it
                pokestops.sort(key=lambda x: distance(position[0], position[1], x['latitude'], x['longitude']))
                gyms.sort(key=lambda x: distance(position[0], position[1], x['latitude'], x['longitude']))

                for pokestop in pokestops:
                    worker = MoveToPokestop(pokestop, self)
                    worker.work()

                #    worker = SeenPokestop(pokestop, self)
                #    hack_chain = worker.work()
                #    if hack_chain > 10:
                #        print('need a rest')
                #        break

                #for gym in gyms:
                #    worker = MoveToGym(fort, self)
                #    worker.work()

                #    worker = SeenGym(gym, self)
                #    hack_chain = worker.work()
                #    if hack_chain > 10:
                #        print('need a rest')
                #        break

        self.scanner_thread._statistic_apply(report)


    def catch_pokemon(self, pokemon):
        return ""
        #worker = PokemonCatch(pokemon, self)
        #return_value = worker.work()

        #if return_value == PokemonCatch.BAG_FULL:
        #    worker = InitialTransfer(self)
        #    worker.work()

        #return return_value

    def drop_item(self, item_id, count):
        self.api.recycle_inventory_item(item_id=item_id, count=count)
        inventory_req = self.api.call()

        # Example of good request response
        #{'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
        return inventory_req

    def inventory_recucle(self):
        pass

    def update_inventory(self):
        self.api.get_inventory()
        response = self.api.call()
        self.inventory = list()
        if 'responses' in response:
            if 'GET_INVENTORY' in response['responses']:
                if 'inventory_delta' in response['responses']['GET_INVENTORY']:
                    if 'inventory_items' in response['responses'][
                            'GET_INVENTORY']['inventory_delta']:
                        for item in response['responses']['GET_INVENTORY'][
                                'inventory_delta']['inventory_items']:
                            if not 'inventory_item_data' in item:
                                continue
                            if not 'item' in item['inventory_item_data']:
                                continue
                            if not 'item_id' in item['inventory_item_data'][
                                    'item']:
                                continue
                            if not 'count' in item['inventory_item_data'][
                                    'item']:
                                continue
                            self.inventory.append(item['inventory_item_data'][
                                'item'])



    def heartbeat(self):
        self.api.get_player()
        self.api.get_hatched_eggs()
        self.api.get_inventory()
        self.api.check_awarded_badges()
        self.api.call()
