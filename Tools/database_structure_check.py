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

for scanner in session_mysql.query(dbScanner).all():
    print 'Проверяем структуру для сканера: {0}.'.format(scanner.id)

    if not session_mysql.query(dbScannerStatistic).filter(dbScannerStatistic.cd_scanner == scanner.id).all():
        print '    Отсутстует статистика, создаем'
        scannerStatistic = dbScannerStatistic()
        scannerStatistic.cd_scanner = scanner.id

        session_mysql.add(scannerStatistic)




for scannerAccount in session_mysql.query(dbScannerAccount).all():
    print 'Проверяем структуру для аккаунта:{0}.'.format(scannerAccount.id)

    if not session_mysql.query(dbScannerAccountStatistic).filter(dbScannerAccountStatistic.cd_account == scannerAccount.id).all():
        print '    Отсутстует статистика'
        scannerAccountStatistic = dbScannerAccountStatistic()
        scannerAccountStatistic.cd_account = scannerAccount.id

        session_mysql.add(scannerAccountStatistic)


session_mysql.commit()
session_mysql.flush()
