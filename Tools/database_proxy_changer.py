#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import time
import argparse
import datetime
import threading

from Interfaces.Config import Config
from Interfaces.MySQL import init_fast as init
from Interfaces.MySQL.Schema import Scanner as dbScanner
from Interfaces.MySQL.Schema import ScannerStatistic as dbScannerStatistic
from Interfaces.MySQL.Schema import ScannerAccount as dbScannerAccount
from Interfaces.MySQL.Schema import ScannerAccountStatistic as dbScannerAccountStatistic

config = Config()

session_maker = init(config)
session_mysql = session_maker()

scanner_index_first = 26
scanner_index_last = 327
scanner_in_server = 25

server_index_first = 2
server_index = server_index_first
server_index_count = 0

proxy_index_first = 2
proxy_index = proxy_index_first
proxy_index_last = 351

for scanner_index in range(scanner_index_first, scanner_index_last):
    scanner = session_mysql.query(dbScanner).filter(dbScanner.cd_account == scanner_index).all()
    if scanner:
        scanner[0].cd_server = server_index

        if proxy_index <= proxy_index_last:
            scanner[0].cd_proxy = proxy_index

        server_index_count += 1
        proxy_index += 1

        if server_index_count == scanner_in_server:
            server_index += 1
            server_index_count = 0


session_mysql.commit()
session_mysql.flush()
session_mysql.close()
