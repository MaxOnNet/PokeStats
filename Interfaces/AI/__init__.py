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
#from Interfaces.AI.Worker import , EvolveAll, MoveToPokestop, ,
from Interfaces.AI.Worker import MoveToPokestop, SeenPokestop, MoveToGym, SeenGym, PokemonCatch, PokemonTransfer
from Interfaces.AI.Worker.Utils import distance
from Interfaces.AI.Human import sleep
from Interfaces.AI.Search import Search
from Interfaces.AI.Metrica import Metrica
from Interfaces.AI.Stepper.Normal import Normal
from Interfaces.AI.Stepper.Spiral import Spiral
from Interfaces.AI.Stepper.Starline import Starline
#from Interfaces.AI.Stepper.Polyline import Polyline
from Interfaces.AI.Stepper.Gymmer import Gymmer
from Interfaces.AI.Stepper.Pokestopper import Pokestopper

from Interfaces.MySQL.Schema import parse_map_cell

from Inventory import InventoryItem

log = logging.getLogger(__name__)


class AI(object):
    def __init__(self, thread):

        self.thread = thread
        self.api = thread.api
        self.geolocation = thread.geolocation
        self.config = thread.config
        self.session = thread.session
        self.scanner = thread.scanner
        self.profile = thread.profile
        self.inventory = thread.inventory
        self.metrica = thread.metrica

        self.delay_action_min = float(self.config.get("AI", "", "delay_action_min", 2))
        self.delay_action_max = float(self.config.get("AI", "", "delay_action_max", 5))
        self.delay_scan = float(self.config.get("AI", "", "delay_scan", 2))

        self.position = (self.api._position_lat, self.api._position_lng, 0)
        self.search = Search(self)
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
        if self.scanner.mode.stepper == "gymmer":
            self.stepper = Gymmer(self)
        if self.scanner.mode.stepper == "pokestopper":
            self.stepper = Pokestopper(self)

        if self.stepper is None:
            log.error("Stepper select error, stepper {0} not found.".format(self.scanner.mode.stepper))
            raise "Stepper select error, stepper {0} not found.".format(self.scanner.mode.stepper)

    def take_step(self):

        worker = PokemonTransfer(self)
        worker.work()

        self.inventory.update()
        self.inventory.recycle()

        self.metrica.take_step()
        self.stepper.take_step()


    def work_on_cell(self, cell, position, seen_pokemon=False, seen_pokestop=False, seen_gym=False):
        self.position = position

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
                            log.debug("Покестоп находится на большом растоянии ({0}), вернемся к нему позже.".format(pokestop_distance))
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
                            sleep(10)

                        self.seen_pokestop[pokestop_id] = time.time()

                        self.inventory.update()
                        self.inventory.recycle()

                        self.metrica.take_ping()

        if seen_gym:
            if 'forts' in cell:
                gyms = [gym for gym in cell['forts'] if 'gym_points' in gym]
                gyms.sort(key=lambda x: distance(position[0], position[1], x['latitude'], x['longitude']))

                if self.scanner.mode.is_lookup or self.scanner.mode.is_defender:
                    for gym in gyms:
                        gym_distance = round(distance(position[0], position[1], gym['latitude'], gym['longitude']))
                        if gym_distance > self.scanner.mode.step*150000:
                            log.debug("Gym находится на большом растоянии ({0}), вернемся к нему позже.".format(gym_distance))
                            continue

                        gym_id = str(gym['id'])

                        if self.scanner.mode.is_defender or self.scanner.mode.is_farm or self.scanner.mode.is_catch:
                            if gym_id in self.seen_gym:
                                if self.seen_gym[gym_id] + 350 > time.time():
                                    continue

                        worker = MoveToGym(gym, self)
                        worker.work()

                        worker = SeenGym(gym, self)
                        hack_chain = worker.work()

                        if hack_chain > 10:
                            sleep(10)

                        self.seen_gym[gym_id] = time.time()

                        self.metrica.take_ping()
        self.metrica.take_ping()

    def catch_pokemon(self, pokemon):
        worker = PokemonCatch(pokemon, self)
        return_value = worker.work()

        if return_value == PokemonCatch.BAG_FULL:
            worker = PokemonTransfer(self)
            worker.work()

        return return_value


    def heartbeat(self):
        self.metrica.take_ping()
        request = self.api.create_request()
        request.get_player()
        request.check_awarded_badges()
        request.call()

