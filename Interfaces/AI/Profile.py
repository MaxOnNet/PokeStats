import datetime
from enum import Enum
import os
import json
import time
import pprint
class Item(Enum):
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

class Profile:
    def __init__(self, api):
        self.api = api
          # get player profile call
        # ----------------------
        self.api.get_player()
        self.api.get_inventory()
        response_dict = self.api.call()
        print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))
        currency_1 = "0"
        currency_2 = "0"

        player = response_dict['responses']['GET_PLAYER']['profile']

        # @@@ TODO: Convert this to d/m/Y H:M:S
        creation_date = datetime.datetime.fromtimestamp(
            player['creation_time'] / 1e3)

        pokecoins = '0'
        stardust = '0'
        balls_stock = self.pokeball_inventory()

        if 'amount' in player['currency'][0]:
            pokecoins = player['currency'][0]['amount']
        if 'amount' in player['currency'][1]:
            stardust = player['currency'][1]['amount']

        print ('[#] Username: {username}'.format(**player))
        print ('[#] Acccount Creation: {}'.format(creation_date))
        print ('[#] Bag Storage: {}/{}'.format(
            self.get_inventory_count('item'), player['max_item_storage']))
        print ('[#] Pokemon Storage: {}/{}'.format(
            self.get_inventory_count('pokemon'), player[
                'max_pokemon_storage']))
        print ('[#] Stardust: {}'.format(stardust))
        print ('[#] Pokecoins: {}'.format(pokecoins))
        print ('[#] PokeBalls: ' + str(balls_stock[1]))
        print ('[#] GreatBalls: ' + str(balls_stock[2]))
        print ('[#] UltraBalls: ' + str(balls_stock[3]))


    def pokeball_inventory(self):
        self.api.get_player().get_inventory()

        inventory_req = self.api.call()
        inventory_dict = inventory_req['responses']['GET_INVENTORY'][
            'inventory_delta']['inventory_items']

        #user_web_inventory = 'web/inventory-%s.json' % (self.config.username)
        #with open(user_web_inventory, 'w') as outfile:
        #    json.dump(inventory_dict, outfile)

        # get player balls stock
        # ----------------------
        balls_stock = {1: 0, 2: 0, 3: 0, 4: 0}

        for item in inventory_dict:
            try:
                print(item['inventory_item_data']['item'])
                item_id = item['inventory_item_data']['item']['item_id']
                item_count = item['inventory_item_data']['item']['count']

                if item_id == Item.ITEM_POKE_BALL.value:
                    print('Poke Ball count: ' + str(item_count))
                    balls_stock[1] = item_count
                if item_id == Item.ITEM_GREAT_BALL.value:
                    print('Great Ball count: ' + str(item_count))
                    balls_stock[2] = item_count
                if item_id == Item.ITEM_ULTRA_BALL.value:
                    print('Ultra Ball count: ' + str(item_count))
                    balls_stock[3] = item_count
            except:
                continue
        return balls_stock

    def item_inventory_count(self, id):
        self.api.get_player().get_inventory()

        inventory_req = self.api.call()
        inventory_dict = inventory_req['responses'][
            'GET_INVENTORY']['inventory_delta']['inventory_items']

        item_count = 0

        for item in inventory_dict:
            try:
                if item['inventory_item_data']['item']['item_id'] == int(id):
                    item_count = item[
                        'inventory_item_data']['item']['count']
            except:
                continue
        return item_count
