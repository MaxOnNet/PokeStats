# -*- coding: utf-8 -*-

import logging
from enum import Enum

from Interfaces.AI.Human import sleep

log = logging.getLogger(__name__)

class InventoryItem(Enum):
    ITEM_UNKNOWN = 0
    ITEM_POKE_BALL = 1
    ITEM_GREAT_BALL = 2
    ITEM_ULTRA_BALL = 3
    ITEM_MASTER_BALL = 4
    ITEM_POTION = 101
    ITEM_SUPER_POTION = 102
    ITEM_HYPER_POTION = 103
    ITEM_MAX_POTION = 104
    ITEM_REVIVE = 201
    ITEM_MAX_REVIVE = 202
    ITEM_LUCKY_EGG = 301
    ITEM_INCENSE_ORDINARY = 401
    ITEM_INCENSE_SPICY = 402
    ITEM_INCENSE_COOL = 403
    ITEM_INCENSE_FLORAL = 404
    ITEM_TROY_DISK = 501
    ITEM_X_ATTACK = 602
    ITEM_X_DEFENSE = 603
    ITEM_X_MIRACLE = 604
    ITEM_RAZZ_BERRY = 701
    ITEM_BLUK_BERRY = 702
    ITEM_NANAB_BERRY = 703
    ITEM_WEPAR_BERRY = 704
    ITEM_PINAP_BERRY = 705
    ITEM_SPECIAL_CAMERA = 801
    ITEM_INCUBATOR_BASIC_UNLIMITED = 901
    ITEM_INCUBATOR_BASIC = 902
    ITEM_POKEMON_STORAGE_UPGRADE = 1001
    ITEM_ITEM_STORAGE_UPGRADE = 1002


class Inventory:
    def __init__(self, thread):
        self.scanner = thread.scanner
        self.session = thread.session

        self.api = thread.api
        self.inventory = list()


    def update(self):
        log.info("Обновляем данные сундука")
        sleep(5)
        response_dict = self.api.get_inventory()

        #response_dict = self.api.call()

        if response_dict and 'status_code' in response_dict:
            if response_dict['status_code'] is 1:
                if 'responses' in response_dict:
                    if 'GET_INVENTORY' in response_dict['responses']:
                        if 'inventory_delta' in response_dict['responses']['GET_INVENTORY']:
                            inventory_res = response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']

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
                                    log.error("Ошибка:{0}".format(e))
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
                                    log.error("Ошибка:{0}".format(e))

                                try:
                                    if 'inventory_item_data' in item:
                                        if 'item' in item['inventory_item_data']:
                                            try:
                                                self.inventory.append(item['inventory_item_data']['item'])
                                            except Exception as e:
                                                log.error("Ошибка:{0}".format(e))

                                            if 'item_id' in item['inventory_item_data']['item'] and 'count' in item['inventory_item_data']['item']:
                                                item_id = item['inventory_item_data']['item']['item_id']
                                                item_count = item['inventory_item_data']['item']['count']



                                                if item_id == InventoryItem.ITEM_POKE_BALL: self.scanner.account.statistic.item_ball_poke = item_count
                                                if item_id == InventoryItem.ITEM_GREAT_BALL: self.scanner.account.statistic.item_ball_great = item_count
                                                if item_id == InventoryItem.ITEM_ULTRA_BALL: self.scanner.account.statistic.item_ball_ultra = item_count
                                                if item_id == InventoryItem.ITEM_MASTER_BALL: self.scanner.account.statistic.item_ball_master = item_count

                                                if item_id == InventoryItem.ITEM_POTION: self.scanner.account.statistic.item_potion = item_count
                                                if item_id == InventoryItem.ITEM_SUPER_POTION: self.scanner.account.statistic.item_potion_super = item_count
                                                if item_id == InventoryItem.ITEM_HYPER_POTION: self.scanner.account.statistic.item_potion_hyper = item_count
                                                if item_id == InventoryItem.ITEM_MAX_POTION: self.scanner.account.statistic.item_potion_master = item_count

                                                if item_id == InventoryItem.ITEM_REVIVE: self.scanner.account.statistic.item_revive = item_count
                                                if item_id == InventoryItem.ITEM_MAX_REVIVE: self.scanner.account.statistic.item_revive_master = item_count

                                                if item_id == InventoryItem.ITEM_RAZZ_BERRY: self.scanner.account.statistic.item_berry_razz = item_count
                                                if item_id == InventoryItem.ITEM_BLUK_BERRY: self.scanner.account.statistic.item_berry_bluk = item_count
                                                if item_id == InventoryItem.ITEM_NANAB_BERRY: self.scanner.account.statistic.item_berry_nanab = item_count
                                                if item_id == InventoryItem.ITEM_WEPAR_BERRY: self.scanner.account.statistic.item_berry_wepar = item_count
                                                if item_id == InventoryItem.ITEM_PINAP_BERRY: self.scanner.account.statistic.item_berry_pinap = item_count
                                except Exception as e:
                                    log.error("Ошибка:{0}".format(e))
                            
                            self.scanner.account.statistic.bag_pokemons = pokecount
                            self.scanner.account.statistic.bag_items = itemcount

                            self.session.commit()
            else:
                log.warning("Получен неверный статус: {0}".format(response_dict['status_code']))





    def pokeball(self):
        self.update()

        balls_stock = {1: 0, 2: 0, 3: 0, 4: 0}

        for item in self.inventory:
            # print(item['inventory_item_data']['item'])
            item_id = int(item['item_id'])
            item_count = int(item['count'])

            if item_id == 1:
                # print('Poke Ball count: ' + str(item_count))
                balls_stock[1] = item_count
            if item_id == 2:
                # print('Great Ball count: ' + str(item_count))
                balls_stock[2] = item_count
            if item_id == 3:
                # print('Ultra Ball count: ' + str(item_count))
                balls_stock[3] = item_count
            if item_id == 4:
                # print('Ultra Ball count: ' + str(item_count))
                balls_stock[4] = item_count

        return balls_stock


    def drop_item(self, item_id, count):
        response_dict = self.api.recycle_inventory_item(item_id=item_id, count=count)
        #response_dict = self.api.call()

        if response_dict and 'status_code' in response_dict:
            if response_dict['status_code'] is 1:
                if 'responses' in response_dict:
                    if 'RECYCLE_INVENTORY_ITEM' in response_dict['responses']:
                        if 'status' in response_dict['responses']['RECYCLE_INVENTORY_ITEM']:
                            if response_dict['responses']['RECYCLE_INVENTORY_ITEM']['status'] is 1:
                                return True
                            else:
                                log.warning("Получен неверный статус: {0}".format(response_dict['responses']['RECYCLE_INVENTORY_ITEM']['status']))
            else:
                log.warning("Получен неверный статус: {0}".format(response_dict['status_code']))

        return False


    def recycle(self):
        for item in self.inventory:
            if "item_id" in item:
                item_db = self.scanner.account.statistic.get_by_item_id(int(item["item_id"]))

                if 'count' in item:
                    if item['count'] > item_db[1]:
                        log.info("Membership {0} is overdraft, drop {1} items".format(item["item_id"], (item['count']-item_db[1])))

                        if not self.drop_item(item["item_id"], (item['count']-item_db[1])):
                            log.warning("Неудалось удалить обьекты из инвентаря")

        self.update()
