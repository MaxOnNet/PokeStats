# -*- coding: utf-8 -*-


import logging
from threading import Thread, Event, currentThread
import queue
import random
from Interfaces.MySQL import init
from Interfaces.MySQL.Schema import parse_map_cell

from Interfaces.AI.Human import sleep, random_lat_long_delta
from Interfaces.AI.Stepper import get_cell_ids
from Interfaces.AI.Worker.Utils import distance, i2f, format_time, encode_coords

from Interfaces.pgoapi.utilities import f2i, h2f
from Interfaces.AI.Stepper.Starline import Starline

log = logging.getLogger(__name__)

class Search:
    def __init__(self, ai):
        self.ai = ai
        self.config = ai.config
        self.api = ai.api
        self.queue = queue.Queue()
        self.threads = list()
        self.thread_event = Event()
        self.thread_create(5)

    def stop(self):
        self.thread_event.set()
        self.queue.join()

    def search(self, lat, lng):
        for index in xrange(20):
            position_queue = {
                'lat': lat + random.uniform(-0.00015*index, 0.00015*index),
                'lng': lng + random.uniform(-0.00015*index, 0.00015*index)
            }
            self.queue.put(position_queue)

    def thread_create(self, count):
        for index in xrange(count):
            thread = Thread(target=self.thread_search, name='{1}-{0}'.format(self.ai.scanner.id, index), args=(self.queue, self.api, self.config, self.thread_event))
            thread.daemon = True
            thread.start()

            self.threads.append(thread)

    def thread_search(self, queue, api_orig, config, event):
        log.info("Start SUB Search thread")
        session_maker = init(config)
        session_mysql = session_maker()


        while not event.isSet():
            position = queue.get()
            log.info("Put work at {} {}".format(position['lat'],position['lng']))
            api = api_orig.copy()
            try:
                cellid = get_cell_ids(position['lat'], position['lng'])
                timestamp = [0, ] * len(cellid)

                api.set_position(position['lat'], position['lng'], 0)
                api.get_map_objects(latitude=f2i(position['lat']), longitude=f2i(position['lng']),  since_timestamp_ms=timestamp, cell_id=cellid)

                response_dict = api.call()

                if response_dict and 'responses' in response_dict:
                    if 'GET_MAP_OBJECTS' in response_dict['responses']:
                        if 'status' in response_dict['responses']['GET_MAP_OBJECTS']:
                            if response_dict['responses']['GET_MAP_OBJECTS']['status'] is 1:
                                for cell in response_dict['responses']['GET_MAP_OBJECTS']['map_cells']:
                                    log.debug( parse_map_cell(cell, session_mysql))
                                    session_mysql.flush()
            except Exception as e:
                log.error("Ошибка в обработке: {}".format(e))

            finally:
                queue.task_done()
        session_mysql.close()
