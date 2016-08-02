# -*- coding: utf-8 -*-

import datetime
import time
import json
import logging
import random
import re
import sys
import math

from Interfaces import analyticts_timer
#from Interfaces.AI.Worker import , EvolveAll, MoveToPokestop, , InitialTransfer
from Interfaces.AI.Worker import MoveToPokestop, SeenPokestop, MoveToGym, SeenGym, PokemonCatch
from Interfaces.AI.Worker.Utils import distance
from Interfaces.AI.Human import sleep

from Interfaces.AI.Stepper.Normal import Normal
from Interfaces.AI.Stepper.Spiral import Spiral
from Interfaces.AI.Stepper.Starline import Starline
#from Interfaces.AI.Stepper.Polyline import Polyline

from Interfaces.MySQL.Schema import parse_map_cell
from Interfaces.Geolocation import Geolocation

from Interfaces import Logger
from Inventory import Item

log = logging.getLogger(__name__)

class AI(object):
    def __init__(self, scanner_thread):

        self.scanner_thread = scanner_thread
        self.api = scanner_thread.api
        self.config = scanner_thread.config
        self.scanner = scanner_thread.scanner

        self.position = self.scanner.location.position

        self.seen_pokestop = {}
        self.seen_gym = {}

        if self.scanner.mode.stepper == "normal":
            self.stepper = Normal(self)
        if self.scanner.mode.stepper == "spiral":
            self.stepper = Spiral(self)
        if self.scanner.mode.stepper == "starline":
            self.stepper = Starline(self)
#        if self.scanner.mode.stepper == "polyline":
#            self.stepper = Polyline(self)

        if self.stepper is None:
            raise "Stepper select error, stepper {0} not found.".format(self.scanner.mode.stepper)

    def take_step(self):
       # worker = InitialTransfer(self)
       # worker.work()
       # InventoryRecycle
       #

        self.inventory_update()
        self.inventory_recycle()

        self.stepper.take_step()


    def work_on_cell(self, cell, position, seen_pokemon=False, seen_pokestop=False, seen_gym=False):
        self.position = position

        #
        #  Парсим данные, плевать на задвоения, логика БД вывезет
        #  парсим целым скопом, для минимизации нагрузки на БД
        self.scanner_thread._statistic_update(parse_map_cell(cell, self.scanner_thread.session_mysql))

        #
        # Искать ли покемонов на пути следования
        #
        if seen_pokemon:
            if self.scanner.mode.is_catch:
                if 'catchable_pokemons' in cell and len(cell['catchable_pokemons']) > 0:
                    cell['catchable_pokemons'].sort(key=lambda x: distance(position[0], position[1], x['latitude'], x['longitude']))

                    for pokemon in cell['catchable_pokemons']:
                        if self.catch_pokemon(pokemon) == PokemonCatch.NO_POKEBALLS:
                            break

                if 'wild_pokemons' in cell and len(cell['wild_pokemons']) > 0:
                    cell['wild_pokemons'].sort(key=lambda x: distance(position[0], position[1], x['latitude'], x['longitude']))

                    for pokemon in cell['wild_pokemons']:
                        if self.catch_pokemon(pokemon) == PokemonCatch.NO_POKEBALLS:
                            break

        #
        # Отвлекаться ли на покестопы
        #
        if seen_pokestop:
            if 'forts' in cell:
                # Only include those with a lat/long
                pokestops = [pokestop for pokestop in cell['forts'] if 'latitude' in pokestop and 'type' in pokestop]
                pokestops.sort(key=lambda x: distance(position[0], position[1], x['latitude'], x['longitude']))

                if self.scanner.mode.is_farm:
                    for pokestop in pokestops:
                        pokestop_distance = round(distance(position[0], position[1], pokestop['latitude'], pokestop['longitude']))
                        if pokestop_distance > self.scanner.mode.step*150000:
                            log.info("Покестоп находится на большом растоянии ({0}), вернемся к нему позже.".format(pokestop_distance))
                            continue

                        pokestop_id = str(pokestop['id'])

                        if pokestop_id in self.seen_pokestop:
                            if self.seen_pokestop[pokestop_id] + 350 > time.time():
                                continue

                        worker = MoveToPokestop(pokestop, self)
                        worker.work()

                        worker = SeenPokestop(pokestop, self)
                        hack_chain = worker.work()

                        if hack_chain > 10:
                            sleep(10*self.scanner.mode.is_human_sleep)

                        self.seen_pokestop[pokestop_id] = time.time()

                        self.inventory_update()
                        self.inventory_recycle()

                        self.scanner_thread._statistic_update({"pokemons": 0, "pokestops": 0, "gyms": 0})


        if seen_gym:
            if 'forts' in cell:
                gyms = [gym for gym in cell['forts'] if 'gym_points' in gym]
                gyms.sort(key=lambda x: distance(position[0], position[1], x['latitude'], x['longitude']))

                for gym in gyms:
                    gym_distance = round(distance(position[0], position[1], gym['latitude'], gym['longitude']))
                    if gym_distance > self.scanner.mode.step*150000:
                        log.info("Покестоп находится на большом растоянии ({0}), вернемся к нему позже.".format(gym_distance))
                        continue

                    gym_id = str(gym['id'])
                    if gym_id in self.seen_gym:
                        if self.seen_gym[gym_id] + 350 > time.time():
                            continue

                    worker = MoveToGym(gym, self)
                    worker.work()

                    worker = SeenGym(gym, self)
                    hack_chain = worker.work()

                    if hack_chain > 10:
                        sleep(10*self.scanner.mode.is_human_sleep)

                    self.seen_gym[gym_id] = time.time()

                    self.scanner_thread._statistic_update({"pokemons": 0, "pokestops": 0, "gyms": 0})

        self.scanner_thread.session_mysql.flush()


    def catch_pokemon(self, pokemon):
        worker = PokemonCatch(pokemon, self)
        return_value = worker.work()

        #if return_value == PokemonCatch.BAG_FULL:
        #    worker = InitialTransfer(self)
        #    worker.work()

        return return_value

    def drop_item(self, item_id, count):
        self.api.recycle_inventory_item(item_id=item_id, count=count)
        inventory_req = self.api.call()

        # Example of good request response
        #{'responses': {'RECYCLE_INVENTORY_ITEM': {'result': 1, 'new_count': 46}}, 'status_code': 1, 'auth_ticket': {'expire_timestamp_ms': 1469306228058L, 'start': '/HycFyfrT4t2yB2Ij+yoi+on778aymMgxY6RQgvrGAfQlNzRuIjpcnDd5dAxmfoTqDQrbz1m2dGqAIhJ+eFapg==', 'end': 'f5NOZ95a843tgzprJo4W7Q=='}, 'request_id': 8145806132888207460L}
        return inventory_req

    def inventory_recycle(self):
        for item in self.inventory:

            item_db = self.scanner.account.statistic.get_by_item_id(int(item["item_id"]))
            if item['count'] > item_db[1]:
                log.info("Membership {0} is overdraft, drop {1} items".format(item["item_id"], (item['count']-item_db[1])))
                self.drop_item(item["item_id"],(item['count']-item_db[1]))

        self.inventory_update()

    def inventory_update(self):
        self.api.get_inventory().get_player()
        response = self.api.call()
        self.inventory = list()
        if 'responses' in response:
            if 'GET_INVENTORY' in response['responses']:
                if 'inventory_delta' in response['responses']['GET_INVENTORY']:
                    if 'inventory_items' in response['responses']['GET_INVENTORY']['inventory_delta']:
                        for item in response['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
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
                            self.inventory.append(item['inventory_item_data']['item'])


    def heartbeat(self):
        self.api.get_player()
        self.api.get_hatched_eggs()
        self.api.get_inventory()
        self.api.check_awarded_badges()
        self.api.call()
