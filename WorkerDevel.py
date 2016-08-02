#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import logging
import time
import argparse
import datetime

from Interfaces.Config import Config
from Interfaces.Scanner import Scanner as tScanner
from Interfaces.MySQL import init_fast as init
from Interfaces.MySQL.Schema import Scanner as dbScanner
from Interfaces.MySQL.Schema import ScannerServer as dbScannerServer

log = logging.getLogger(__name__)

scanner_id = 11

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(module)15s] [%(levelname)7s] [%(threadName)5s] %(message)s')

    logging.getLogger("peewee").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("Interfaces.pgoapi.pgoapi").setLevel(logging.WARNING)
    logging.getLogger("Interfaces.pgoapi.rpc_api").setLevel(logging.WARNING)

    logging.getLogger("Interfaces.AI").setLevel(logging.INFO)

    threads = []

    scanner = tScanner(scanner_id)
    scanner.start()
    time.sleep(6000)
