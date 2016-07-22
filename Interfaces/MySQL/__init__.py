#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Interfaces.MySQL.Schema import *
from Interfaces.MySQL.Types import PasswordType
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.orm import scoped_session


def init(config):
    mysql_engine = create_engine('mysql+pymysql://{0}:{1}@{2}'.format(
        config.get("database", "mysql", "user"),
        config.get("database", "mysql", "password"),
        config.get("database", "mysql", "server")
    ))

    mysql_engine.execute("CREATE DATABASE IF NOT EXISTS {0} "
                         "DEFAULT CHARACTER SET = '{1}' DEFAULT COLLATE 'utf8_unicode_ci'".format(
        config.get("database", "mysql", "database"),
        config.get("database", "mysql", "charset", "utf8")
    ))

    # Go ahead and use this engine
    db_engine = create_engine('mysql+pymysql://{0}:{1}@{2}/{3}?charset={4}'.format(
        config.get("database", "mysql", "user"),
        config.get("database", "mysql", "password"),
        config.get("database", "mysql", "server"),
        config.get("database", "mysql", "database"),
        config.get("database", "mysql", "charset", "utf8")
    ))

    Base.metadata.create_all(db_engine)

    return scoped_session(
        sessionmaker(
                autoflush=True,
                autocommit=False,
                bind=db_engine
            )
        )

