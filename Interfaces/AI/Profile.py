import datetime
from enum import Enum
import os
import json
import time
import pprint

from Interfaces.AI.Inventory import Item

class Profile:
    def __init__(self, scanner_thread):
        self.scanner = scanner_thread.scanner
        self.session_mysql = scanner_thread.session_mysql

        self.api = scanner_thread.api

    def update_inventory(self):
        self.api.get_player().get_inventory()

        inventory_req = self.api.call()
        inventory_res = inventory_req['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

        pokecount = 0
        itemcount = 1

        for item in inventory_res:
            try:
                if 'inventory_item_data' in item:
                    if 'pokemon_data' in item['inventory_item_data']:
                        pokecount = pokecount + 1

                    if 'item' in item['inventory_item_data']:
                        if 'count' in item['inventory_item_data']['item']:
                            itemcount = itemcount + item['inventory_item_data']['item']['count']
            except Exception as e:
                pass
            try:
                if 'inventory_item_data' in item:
                    if 'player_stats' in item['inventory_item_data']:
                        playerdata = item['inventory_item_data']['player_stats']

                        if 'level' in playerdata: self.scanner.account.statistic.level = playerdata['level']

                        if 'experience' in playerdata: self.scanner.account.statistic.experience = playerdata['experience']

                        if 'next_level_xp' in playerdata and 'experience' in playerdata: self.scanner.account.statistic.experience_to_level = (int(playerdata.get('next_level_xp', 0)) -int(playerdata.get('experience', 0)))

                        if 'pokemons_captured' in playerdata: self.scanner.account.statistic.catched_pokemons = playerdata['pokemons_captured']

                        if 'poke_stop_visits' in playerdata: self.scanner.account.statistic.visited_pokestops = playerdata['poke_stop_visits']

                        #if 'km_walked' in playerdata: self.scanner.account.statistic.walked = playerdata['km_walked']
            except Exception as e:
                pass
            try:
                item_id = item['inventory_item_data']['item']['item_id']
                item_count = item['inventory_item_data']['item']['count']

                if item_id == Item.ITEM_POKE_BALL: self.scanner.account.statistic.item_ball_poke = item_count
                if item_id == Item.ITEM_GREAT_BALL: self.scanner.account.statistic.item_ball_great = item_count
                if item_id == Item.ITEM_ULTRA_BALL: self.scanner.account.statistic.item_ball_ultra = item_count
                if item_id == Item.ITEM_MASTER_BALL: self.scanner.account.statistic.item_ball_master = item_count

                if item_id == Item.ITEM_POTION: self.scanner.account.statistic.item_potion = item_count
                if item_id == Item.ITEM_SUPER_POTION: self.scanner.account.statistic.item_potion_super = item_count
                if item_id == Item.ITEM_HYPER_POTION: self.scanner.account.statistic.item_potion_hyper = item_count
                if item_id == Item.ITEM_MAX_POTION: self.scanner.account.statistic.item_potion_master = item_count

                if item_id == Item.ITEM_REVIVE: self.scanner.account.statistic.item_revive = item_count
                if item_id == Item.ITEM_MAX_REVIVE: self.scanner.account.statistic.item_revive_master = item_count

                if item_id == Item.ITEM_RAZZ_BERRY: self.scanner.account.statistic.item_berry_razz = item_count
                if item_id == Item.ITEM_BLUK_BERRY: self.scanner.account.statistic.item_berry_bluk = item_count
                if item_id == Item.ITEM_NANAB_BERRY: self.scanner.account.statistic.item_berry_nanab = item_count
                if item_id == Item.ITEM_WEPAR_BERRY: self.scanner.account.statistic.item_berry_wepar = item_count
                if item_id == Item.ITEM_PINAP_BERRY: self.scanner.account.statistic.item_berry_pinap = item_count
            except Exception as e:
                pass

        self.scanner.account.statistic.bag_pokemons = pokecount
        self.scanner.account.statistic.bag_items = itemcount

        self.session_mysql.commit()
        #self.session_mysql.flush()

    def update_profile(self):

        self.api.get_player()
        profile_req = self.api.call()

        profile_res = profile_req['responses']['GET_PLAYER']['player_data']
        try:
            self.scanner.account.statistic.username = profile_res['username']
            self.scanner.account.statistic.date_start = datetime.datetime.fromtimestamp(profile_res['creation_timestamp_ms'] / 1e3)

            if 'amount' in profile_res['currencies'][0]:
                self.scanner.account.statistic.pokecoins = profile_res['currencies'][0]['amount']
            if 'amount' in profile_res['currencies'][1]:
                self.scanner.account.statistic.stardust = profile_res['currencies'][1]['amount']
        except:
            pass

        self.session_mysql.commit()
        #self.session_mysql.flush()