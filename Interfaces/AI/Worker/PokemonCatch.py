# -*- coding: utf-8 -*-

import time
import logging
import json
import os

from sets import Set

from Interfaces.AI.Worker.Utils import distance
from Interfaces.AI.Human import sleep, action_delay, normalized_reticle_size, spin_modifier
from Interfaces.AI.Inventory import InventoryItem

log = logging.getLogger(__name__)


class PokemonCatch(object):
    BAG_FULL = 'bag_full'
    NO_POKEBALLS = 'no_pokeballs'

    def __init__(self, pokemon, ai):
        self.ai = ai
        self.api = ai.api
        self.config = ai.config
        self.session = ai.session
        self.position = ai.position
        self.stepper = ai.stepper
        self.inventory = ai.inventory

        self.pokemon = pokemon
        self.pokemon_transfer = bool(self.config.get("AI",  self.__class__.__name__, "use_transfer", 1))
        self.pokemon_evolve = bool(self.config.get("AI",  self.__class__.__name__, "use_evolve", 1))

        self.data_pokemon = {}
        self.data_transfer = {}

        if os.path.isfile(self.config.get("AI",  self.__class__.__name__, "data_pokemon")):
            with open(self.config.get("AI",  self.__class__.__name__, "data_pokemon")) as data:
                self.data_pokemon = json.load(data)

        if os.path.isfile(self.config.get("AI",  self.__class__.__name__, "data_transfer")):
            with open(self.config.get("AI",  self.__class__.__name__, "data_transfer")) as data:
                self.data_transfer = json.load(data)

    def work(self):
        encounter_id = self.pokemon['encounter_id']
        spawnpoint_id = self.pokemon['spawn_point_id']
        player_latitude = self.pokemon['latitude']
        player_longitude = self.pokemon['longitude']

        response_dict = self.api.encounter(encounter_id=encounter_id, spawn_point_id=spawnpoint_id,
                           player_latitude=player_latitude, player_longitude=player_longitude)
        #response_dict = self.api.call()

        if response_dict and 'responses' in response_dict:
            if 'ENCOUNTER' in response_dict['responses']:
                if 'status' in response_dict['responses']['ENCOUNTER']:
                    if response_dict['responses']['ENCOUNTER']['status'] is 7:
                        log.warning('[x] Pokemon Bag is full!')
                        return PokemonCatch.BAG_FULL

                    if response_dict['responses']['ENCOUNTER']['status'] is 1:
                        cp = 0
                        total_IV = 0
                        if 'wild_pokemon' in response_dict['responses']['ENCOUNTER']:
                            pokemon = response_dict['responses']['ENCOUNTER']['wild_pokemon']
                            catch_rate = response_dict['responses']['ENCOUNTER']['capture_probability']['capture_probability'] # 0 = pokeballs, 1 great balls, 3 ultra balls

                            if 'pokemon_data' in pokemon and 'cp' in pokemon['pokemon_data']:
                                cp = pokemon['pokemon_data']['cp']
                                iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']

                                for individual_stat in iv_stats:
                                    try:
                                        total_IV += pokemon['pokemon_data'][individual_stat]
                                    except:
                                        pokemon['pokemon_data'][individual_stat] = 0
                                        continue

                                pokemon_potential = round((total_IV / 45.0), 2)
                                pokemon_num = int(pokemon['pokemon_data']['pokemon_id']) - 1
                                pokemon_name = self.data_pokemon[int(pokemon_num)]['Name']

                                log.info('A Wild {} appeared! [CP {}] [Potential {}]'.format(pokemon_name, cp, pokemon_potential))

                                log.info('IV [Stamina/Attack/Defense] = [{}/{}/{}]'.format(
                                    pokemon['pokemon_data']['individual_stamina'],
                                    pokemon['pokemon_data']['individual_attack'],
                                    pokemon['pokemon_data']['individual_defense']
                                ))

                        # Simulate app
                        action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

                        balls_stock = self.inventory.pokeball()

                        while(True):

                            pokeball = 1 # default:poke ball

                            if balls_stock[1] <= 0: # if poke ball are out of stock
                                if balls_stock[2] > 0: # and player has great balls in stock...
                                    pokeball = 2 # then use great balls
                                elif balls_stock[3] > 0: # or if great balls are out of stock too, and player has ultra balls...
                                    pokeball = 3 # then use ultra balls
                                else:
                                    pokeball = 0 # player doesn't have any of pokeballs, great balls or ultra balls

                            while(pokeball < 3):
                                if catch_rate[pokeball-1] < 0.35 and balls_stock[pokeball+1] > 0:
                                    # if current ball chance to catch is under 35%, and player has better ball - then use it
                                    pokeball = pokeball+1 # use better ball
                                else:
                                    break

                            # @TODO, use the best ball in stock to catch VIP (Very Important Pokemon: Configurable)

                            if pokeball is 0:
                                log.warning(balls_stock)
                                log.warning('Out of pokeballs, switching to farming mode...')
                                # Begin searching for pokestops.
                                return PokemonCatch.NO_POKEBALLS

                            balls_stock[pokeball] = balls_stock[pokeball] - 1
                            success_percentage = '{0:.2f}'.format(catch_rate[pokeball-1]*100)
                            log.info('Using {} (chance: {}%)... ({} left!)'.format(
                                pokeball,
                                success_percentage, 
                                balls_stock[pokeball]
                            ))

                            id_list1 = self.count_pokemon_inventory()
                            response_dict = self.api.catch_pokemon(encounter_id=encounter_id,
                                                   pokeball=pokeball,
                                                   normalized_reticle_size=normalized_reticle_size(1.5),
                                                   spawn_point_id=spawnpoint_id,
                                                   hit_pokemon=1,
                                                   spin_modifier=spin_modifier(0.9),
                                                   normalized_hit_position=1)
                            #response_dict = self.api.call()

                            if response_dict and \
                                'responses' in response_dict and \
                                'CATCH_POKEMON' in response_dict['responses'] and \
                                    'status' in response_dict['responses']['CATCH_POKEMON']:
                                status = response_dict['responses']['CATCH_POKEMON']['status']
                                if status is 2:
                                    log.warning('Attempted to capture {}- failed.. trying again!'.format(pokemon_name))
                                    action_delay(self.ai.delay_action_min, self.ai.delay_action_max)
                                    continue
                                if status is 3:
                                    log.warning('Oh no! {} vanished! :('.format(pokemon_name))
                                if status is 1:
                                    log.info('Captured {}! [CP {}] [IV {}]'.format(pokemon_name, cp, pokemon_potential))

                                    id_list2 = self.count_pokemon_inventory()

                                    if self.pokemon_evolve:
                                        try:
                                            pokemon_to_transfer = list(Set(id_list2) - Set(id_list1))
                                            response_dict = self.api.evolve_pokemon(pokemon_id=pokemon_to_transfer[0])
                                            #response_dict = self.api.call()
                                            status = response_dict['responses']['EVOLVE_POKEMON']['result']
                                            if status == 1:
                                                log.info('{} has been evolved!'.format(pokemon_name))
                                            else:
                                                log.warning('Failed to evolve {}!'.format(pokemon_name))
                                        except Exception as e:
                                            log.error('Failed while evolve {}!'.format(e))

                                    if self.should_release_pokemon(pokemon_name, cp, pokemon_potential, response_dict):
                                        # Transfering Pokemon
                                        pokemon_to_transfer = list(
                                           Set(id_list2) - Set(id_list1))

                                        if len(pokemon_to_transfer) == 0:
                                            raise RuntimeError(
                                                'Trying to transfer 0 pokemons!')

                                        self.transfer_pokemon(pokemon_to_transfer[0])
                                        log.info('{} has been exchanged for candy!'.format(pokemon_name))
                                    else:
                                        log.info('Captured {}! [CP {}]'.format(pokemon_name, cp))
                            break
        action_delay(self.ai.delay_action_min, self.ai.delay_action_max)

    def _transfer_low_cp_pokemon(self, value):
        response_dict = self.api.get_inventory()
        #response_dict = self.api.call()
        self._transfer_all_low_cp_pokemon(value, response_dict)

    def _transfer_all_low_cp_pokemon(self, value, response_dict):
        try:
            reduce(dict.__getitem__, [
                   "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                try:
                    reduce(dict.__getitem__, [
                           "inventory_item_data", "pokemon"], item)
                except KeyError:
                    pass
                else:
                    pokemon = item['inventory_item_data']['pokemon']
                    self._execute_pokemon_transfer(value, pokemon)
                    time.sleep(1.2)

    def _execute_pokemon_transfer(self, value, pokemon):
        if 'cp' in pokemon and pokemon['cp'] < value:
            response_dict = self.api.release_pokemon(pokemon_id=pokemon['id'])
            #response_dict = self.api.call()

    def transfer_pokemon(self, pid):
        response_dict = self.api.release_pokemon(pokemon_id=pid)
        #response_dict = self.api.call()

    def count_pokemon_inventory(self):
        response_dict = self.api.get_inventory()
        #response_dict = self.api.call()
        id_list = []
        return self.counting_pokemon(response_dict, id_list)

    def counting_pokemon(self, response_dict, id_list):
        try:
            reduce(dict.__getitem__, [
                   "responses", "GET_INVENTORY", "inventory_delta", "inventory_items"], response_dict)
        except KeyError:
            pass
        else:
            for item in response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']:
                try:
                    reduce(dict.__getitem__, [
                           "inventory_item_data", "pokemon_data"], item)
                except KeyError:
                    pass
                else:
                    pokemon = item['inventory_item_data']['pokemon_data']
                    if pokemon.get('is_egg', False):
                        continue
                    id_list.append(pokemon['id'])

        return id_list

    def should_release_pokemon(self, pokemon_name, cp, iv, response_dict):
        if self._check_always_capture_exception_for(pokemon_name):
            return False
        else:
            release_config = self._get_release_config_for(pokemon_name)
            cp_iv_logic = release_config.get('cp_iv_logic')
            if not cp_iv_logic:
                cp_iv_logic = self._get_release_config_for('any').get('cp_iv_logic', 'and')

            release_results = {
                'cp':               False,
                'iv':               False,
            }

            if 'release_under_cp' in release_config:
                min_cp = release_config['release_under_cp']
                if cp < min_cp:
                    release_results['cp'] = True

            if 'release_under_iv' in release_config:
                min_iv = release_config['release_under_iv']
                if iv < min_iv:
                    release_results['iv'] = True

            if release_config.get('always_release'):
                return True

            logic_to_function = {
                'or': lambda x, y: x or y,
                'and': lambda x, y: x and y
            }

            log.debug(
                "Release config for {}: CP {} {} IV {}".format(
                    pokemon_name,
                    release_config['release_under_cp'],
                    cp_iv_logic,
                    release_config['release_under_iv']
                )
            )

            return logic_to_function[cp_iv_logic](*release_results.values())

    def _get_release_config_for(self, pokemon):
        release_config = self.data_transfer.get(pokemon)
        if not release_config:
            release_config = self.data_transfer['any']
        return release_config

    def _get_exceptions(self):
        exceptions = self.data_transfer.get('exceptions')
        if not exceptions:
            return None
        return exceptions

    def _get_always_capture_list(self):
        exceptions = self._get_exceptions()
        if not exceptions:
            return []
        always_capture_list = exceptions['always_capture']
        if not always_capture_list:
            return []
        return always_capture_list

    def _check_always_capture_exception_for(self, pokemon_name):
        always_capture_list = self._get_always_capture_list()
        if not always_capture_list:
            return False
        else:
            for pokemon in always_capture_list:
                if pokemon_name == str(pokemon):
                    return True
        return False
