# -*- coding: utf-8 -*-


import logging
from threading import Thread, Event, currentThread
import queue
import random

from Interfaces.MySQL.Schema import parse_map_cell

from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Worker.Utils import distance, i2f, format_time, encode_coords

from Interfaces.pgoapi.utilities import f2i, h2f, get_cell_ids
from Interfaces.AI.Stepper.Starline import Starline
from Interfaces.AI.Stepper.Spiral import Spiral
from Interfaces.AI.Stepper.Normal import Normal

log = logging.getLogger(__name__)


class Search:
    def __init__(self, ai):
        self.thread = ai.thread
        self.api = ai.api
        self.geolocation = ai.geolocation
        self.config = ai.thread.config
        self.scanner = ai.scanner
        self.profile = ai.profile
        self.inventory = ai.inventory

        self.requests = queue.Queue()
        self.response = queue.Queue()

        self.step = self.scanner.mode.step
        self.distance = self.scanner.location.distance * 1000

        self.threads = list()
        self.thread_event = Event()

        if self.scanner.mode.is_search:
            self.thread_create(4)

    def stop(self):
        self.thread_event.set()
        self.requests.join()

    def search(self, lat, lng):
        if self.scanner.mode.is_search:
            log.debug("Start Search at {} {}".format(lat, lng))

            coords = Starline.generate_coords(lat, lng, self.step, self.distance/2)
            log.debug(self.geolocation.get_google_polilyne(coords))
            for coord in coords:
                self.requests.put(coord)

            #coords = Starline.generate_coords(lat, lng, self.step, self.distance)
            #log.debug(self.geolocation.get_google_polilyne(coords))
            #for coord in coords:
            #    self.requests.put(coord)

    def thread_create(self, count):
        for index in xrange(count):
            thread = Thread(target=self.thread_search, name='{1}-{0}'.format(self.scanner.id, index), args=(self.requests, self.response, self.api, self.thread_event))
            thread.daemon = True
            thread.start()

            self.threads.append(thread)

    def thread_search(self, requests, response, api_orig,event):
        log.info("Поток начал свою работу")
        sleep(5)
        while not event.isSet():
            position = requests.get()
            log.debug("Put work at {} {}".format(position['lat'], position['lng']))
            sleep(4)
            api = api_orig.copy()
            try:
                response_index = 0

                while response_index < 5:
                    cellid = get_cell_ids(position['lat'], position['lng'])
                    timestamp = [1, ] * len(cellid)

                    api.set_position(position['lat'], position['lng'], 0)
                    response_dict = api.get_map_objects(latitude=f2i(position['lat']), longitude=f2i(position['lng']),  since_timestamp_ms=timestamp, cell_id=cellid)

                    if response_dict and 'status_code' in response_dict:
                        if response_dict['status_code'] is 1:
                            if 'responses' in response_dict:
                                if 'GET_MAP_OBJECTS' in response_dict['responses']:
                                    if 'status' in response_dict['responses']['GET_MAP_OBJECTS']:
                                        if response_dict['responses']['GET_MAP_OBJECTS']['status'] is 1:
                                            map_cells = response_dict['responses']['GET_MAP_OBJECTS']['map_cells']

                                            log.debug("Получена информация о карте в размере {0} ячеек".format(len(map_cells)))
                                            for map_cell in map_cells:
                                                self.response.put(map_cell)

                                            response_index = 999
                                        else:
                                            log.warning("Получен неверный статус: {0}".format(response_dict['responses']['GET_MAP_OBJECTS']['status']))
                        else:
                            log.debug("Получен неверный статус: {0}".format(response_dict['status_code']))

                            if response_dict['status_code'] == 52:
                                response_index += 1
                                sleep(5)

            except Exception as e:
                log.error("Ошибка в обработке дочернего потока: {}".format(e))

            finally:
                requests.task_done()

        log.info("Поток завершил работу")
