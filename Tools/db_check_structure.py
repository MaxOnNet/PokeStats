#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import time
import argparse
import datetime
import threading

from Interfaces.Config import Config
from Interfaces.Scanner import Scanner as tScanner
from Interfaces.MySQL import init_fast as init
from Interfaces.MySQL.Schema import Scanner as dbScanner
from Interfaces.MySQL.Schema import ScannerStatistic as dbScannerStatistic
from Interfaces.MySQL.Schema import ScannerAccount as dbScannerAccount
from Interfaces.MySQL.Schema import ScannerAccountStatistic as dbScannerAccountStatistic

config = Config()

session_maker = init(config)
session_mysql = session_maker()

p_i = 2
s_i = 2
s_ii =0
for p_i in xrange(326):
    if p_i > 26:
        print s_i
        scanner = session_mysql.query(dbScanner).filter(dbScanner.cd_account == p_i).all()
        if scanner:
            scanner[0].cd_server = s_i

            s_ii +=1
            if s_ii == 25:
                s_ii = 0
                s_i += 1

session_mysql.commit()
session_mysql.flush()
sys.exit(0)
#27-326
proxy_index = 2
for scanner in session_mysql.query(dbScanner).all():
    print 'Проверяем структуру для сканера:{0}.'.format(scanner.id)

    if not session_mysql.query(dbScannerStatistic).filter(dbScannerStatistic.cd_scanner == scanner.id).all():
        print '    Отсутстует статистика'
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
