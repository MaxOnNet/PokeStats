#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.orm import relationship
from sqlalchemy.orm import object_session

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from datetime import datetime, timedelta

log = logging.getLogger(__name__)
Base = declarative_base()


class ScannerServer(Base):
    __tablename__ = 'scanner_server'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(Integer(), primary_key=True, autoincrement=True, doc="")
    name = Column(String(64), nullable=False, doc="")
    description = Column(String(256), nullable=False, doc="")

    scanners = relationship("Scanner")


class ScannerAccount(Base):
    __tablename__ = 'scanner_account'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}
    id = Column(Integer(), primary_key=True, autoincrement=True, doc="")

    username = Column(String(64), nullable=False, doc="")
    password = Column(String(64), nullable=False, doc="")
    service = Column(String(64), nullable=False, doc="")

    is_enable = Column(Boolean(), default=False)
    is_active = Column(Boolean(), default=False)

    state = Column(String(256), nullable=False, doc="")
    description = Column(String(64), nullable=False, doc="")

    statistic = relationship("ScannerAccountStatistic", uselist=False)


class ScannerAccountStatistic(Base):
    __tablename__ = 'scanner_account_statistic'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(Integer(), primary_key=True, autoincrement=True, doc="")
    cd_account = Column(Integer(), ForeignKey('scanner_account.id'), default=0, nullable=False, doc="")

    username = Column(String(64), nullable=False, doc="")
    date_start = Column(DateTime(), nullable=False, default=func.now())

    stardust = Column(Integer(), default=0, nullable=False)
    pokecoins = Column(Integer(), default=0, nullable=False)

    level = Column(Integer(), default=0, nullable=False)
    experience = Column(Integer(), default=0, nullable=False)
    experience_to_level = Column(Integer(), default=0, nullable=False)

    bag_items = Column(Integer(), default=0, nullable=False)
    bag_pokemons = Column(Integer(), default=0, nullable=False)

    visited_pokestops = Column(Integer(), default=0, nullable=False)
    catched_pokemons = Column(Integer(), default=0, nullable=False)

    item_ball_poke = Column(Integer(), default=0, nullable=False)
    item_ball_poke_max = Column(Integer(), default=25, nullable=False)
    item_ball_great = Column(Integer(), default=0, nullable=False)
    item_ball_great_max = Column(Integer(), default=35, nullable=False)
    item_ball_ultra = Column(Integer(), default=0, nullable=False)
    item_ball_ultra_max = Column(Integer(), default=45, nullable=False)
    item_ball_master = Column(Integer(), default=0, nullable=False)
    item_ball_master_max = Column(Integer(), default=50, nullable=False)

    item_potion = Column(Integer(), default=0, nullable=False)
    item_potion_max = Column(Integer(), default=20, nullable=False)
    item_potion_super = Column(Integer(), default=0, nullable=False)
    item_potion_super_max = Column(Integer(), default=20, nullable=False)
    item_potion_hyper = Column(Integer(), default=0, nullable=False)
    item_potion_hyper_max = Column(Integer(), default=20, nullable=False)
    item_potion_master = Column(Integer(), default=0, nullable=False)
    item_potion_master_max = Column(Integer(), default=20, nullable=False)

    item_revive = Column(Integer(), default=0, nullable=False)
    item_revive_max = Column(Integer(), default=10, nullable=False)
    item_revive_master = Column(Integer(), default=0, nullable=False)
    item_revive_master_max = Column(Integer(), default=10, nullable=False)

    item_berry_razz = Column(Integer(), default=0, nullable=False)
    item_berry_razz_max = Column(Integer(), default=10, nullable=False)
    item_berry_bluk = Column(Integer(), default=0, nullable=False)
    item_berry_bluk_max = Column(Integer(), default=10, nullable=False)
    item_berry_nanab = Column(Integer(), default=0, nullable=False)
    item_berry_nanab_max = Column(Integer(), default=10, nullable=False)
    item_berry_wepar = Column(Integer(), default=0, nullable=False)
    item_berry_wepar_max = Column(Integer(), default=10, nullable=False)
    item_berry_pinap = Column(Integer(), default=0, nullable=False)
    item_berry_pinap_max = Column(Integer(), default=10, nullable=False)

    date_create = Column(DateTime(), nullable=False, default=func.now())
    date_change = Column(DateTime(), nullable=False, default=func.now(), onupdate=func.now())


class ScannerLocation(Base):
    __tablename__ = 'scanner_location'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(Integer(), primary_key=True, autoincrement=True, doc="")
    address = Column(String(254), nullable=False, doc="")
    description = Column(String(256), nullable=False, doc="")

    latitude = Column(Float(), default=0)
    longitude = Column(Float(), default=0)

    steps = Column(Integer(), default=10)
    walk = Column(Integer(), default=39)

    use_ai = Column(Boolean(), default=False)
    use_ai_stepper = Column(Boolean(), default=False)

    def fix(self, geolocation):
        if self.latitude == 0 or self.longitude == 0:
            position = geolocation.get_position_by_name(self.address)

            self.latitude = position[0]
            self.longitude = position[1]

            object_session(self).commit()
            object_session(self).flush()

    @hybrid_property
    def position(self):
        return [self.latitude, self.longitude, 0]


class Scanner(Base):
    __tablename__ = 'scanner'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(Integer(), primary_key=True, autoincrement=True, doc="")

    cd_server = Column(Integer(), ForeignKey('scanner_server.id'), default=0, nullable=False, doc="")
    cd_account = Column(Integer(), ForeignKey('scanner_account.id'), default=0, nullable=False, doc="")
    cd_location = Column(Integer(), ForeignKey('scanner_location.id'), default=0, nullable=False, doc="")

    is_enable = Column(Boolean(), default=False)
    is_active = Column(Boolean(), default=False)

    state = Column(String(256), nullable=False, doc="")

    latitude = Column(Float(), default=0, nullable=False)
    longitude = Column(Float(), default=0, nullable=False)

    date_create = Column(DateTime(), nullable=False, default=func.now())
    date_change = Column(DateTime(), nullable=False, default=func.now(), onupdate=func.now())

    server = relationship("ScannerServer", backref="Scanner")
    account = relationship("ScannerAccount", backref="Scanner")
    location = relationship("ScannerLocation", backref="Scanner")

    statistic = relationship("ScannerStatistic", uselist=False)


class ScannerStatistic(Base):
    __tablename__ = 'scanner_statistic'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(Integer(), primary_key=True, autoincrement=True, doc="")

    cd_scanner = Column(Integer(), ForeignKey('scanner.id'), default=0, nullable=False, doc="")

    gyms = Column(Integer(), default=0, nullable=False)
    pokestops = Column(Integer(), default=0, nullable=False)
    pokemons = Column(Integer(), default=0, nullable=False)


    date_start = Column(DateTime(), nullable=False, default=func.now())
    date_create = Column(DateTime(), nullable=False, default=func.now())
    date_change = Column(DateTime(), nullable=False, default=func.now(), onupdate=func.now())



class Pokemon(Base):
    __tablename__ = 'pokemon'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(Integer(), primary_key=True, autoincrement=True, doc="")

    name = Column(String(64), nullable=False, doc="")
    group = Column(String(64), nullable=False, doc="")
    color = Column(String(16), nullable=False, doc="")
    zoom = Column(Float(), nullable=False, default=1)
    evolution = Column(Integer(), nullable=False, default=1)


class PokemonSpawnpoint(Base):
    __tablename__ = 'pokemon_spawnpoint'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(String(64), doc="")
    cd_encounter = Column(String(64), primary_key=True, doc="")
    cd_pokemon = Column(Integer(), ForeignKey('pokemon.id'), default=0, nullable=False, doc="")

    latitude = Column(Float())
    longitude = Column(Float())

    date_disappear = Column(DateTime(), nullable=True)
    date_till_hidden = Column(Integer(), default=0, nullable=False)
    date_create = Column(DateTime(), nullable=False, default=func.now())
    date_change = Column(DateTime(), nullable=False, default=func.now(), onupdate=func.now())

    pokemon = relationship("Pokemon", backref="PokemonSpawnpoint")

    #
    @property
    def date_disappear_fix(self):
        return self.date_disappear - timedelta(hours=6)

    @classmethod
    def get_active(cls, session):
        return session.query(PokemonSpawnpoint).filter(PokemonSpawnpoint.date_disappear > datetime.now())
        #return session.query(PokemonSpawnpoint)


class Pokestop(Base):
    __tablename__ = 'pokestop'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(String(64), primary_key=True, doc="")

    is_enabled = Column(Boolean(),default=False)

    latitude = Column(Float())
    longitude = Column(Float())

    name = Column(String(256), default="", doc="")
    address = Column(String(256), default="", doc="")
    description = Column(String(256), default="", doc="")
    image_url = Column(String(256), default="", doc="")

    date_modified = Column(DateTime(), nullable=True)
    date_lure_expiration = Column(DateTime(), nullable=True)

    date_create = Column(DateTime(), nullable=False, default=func.now())
    date_change = Column(DateTime(), nullable=False, default=func.now(), onupdate=func.now())


class Team(Base):
    __tablename__ = 'team'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(Integer(), primary_key=True, doc="")

    name = Column(String(64), nullable=False, doc="")

    UNCONTESTED = 0
    TEAM_MYSTIC = 1
    TEAM_VALOR = 2
    TEAM_INSTINCT = 3


class Gym(Base):
    __tablename__ = 'gym'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(String(64), primary_key=True, doc="")
    cd_team = Column(Integer(), nullable=False, doc="")
    cd_guard_pokemon = Column(Integer(), default=0, nullable=False, doc="")

    is_enabled = Column(Boolean(), default=False)

    latitude = Column(Float())
    longitude = Column(Float())

    prestige = Column(Float(), default=0, nullable=False)

    name = Column(String(256), default="", doc="")
    address = Column(String(256), default="", doc="")
    description = Column(String(256), default="", doc="")
    image_url = Column(String(256), default="", doc="")

    date_modified = Column(DateTime(), nullable=True)
    date_create = Column(DateTime(), nullable=False, default=func.now())
    date_change = Column(DateTime(), nullable=False, default=func.now(), onupdate=func.now())


def parse_map(map_dict, session):
    count_pokemons = 0
    count_gyms = 0
    count_pokestops = 0

    if not 'GET_MAP_OBJECTS' in map_dict['responses']:
        print map_dict['responses']
    cells = map_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    for cell in cells:
        count_pokemons += parse_pokemon_cell(cell, session)

        for f in cell.get('forts', []):
            if f.get('type') == 1:  # Pokestops
                count_pokemons + parse_pokestop(f, session)
            else:  # Currently, there are only stops and gyms
                count_gyms + parse_gym(f, session)
    session.flush()

    return {"gyms": count_gyms, "pokestops": count_pokestops, "pokemons": count_pokemons}

def parse_fort(fort_id, fort_type, map_dict, session):
    fort_name = ""
    fort_image = ""
    fort_description = ""

    if 'responses' in map_dict \
            and'FORT_DETAILS' in map_dict['responses'] \
            and 'name' in map_dict['responses']['FORT_DETAILS']:
        fort_details = map_dict['responses']['FORT_DETAILS']
        fort_name = fort_details['name'].encode('utf8', 'replace')


    if 'responses' in map_dict \
            and'FORT_DETAILS' in map_dict['responses'] \
            and 'image_urls' in map_dict['responses']['FORT_DETAILS']:
        fort_details = map_dict['responses']['FORT_DETAILS']
        fort_image = fort_details['image_urls'][0].encode('utf8', 'replace')

    if 'responses' in map_dict \
            and'FORT_DETAILS' in map_dict['responses'] \
            and 'description' in map_dict['responses']['FORT_DETAILS']:
        fort_details = map_dict['responses']['FORT_DETAILS']
        fort_description = fort_details['description'].encode('utf8', 'replace')

    if fort_type == 1:
        pokestop = session.query(Pokestop).get(fort_id)

        pokestop.name = fort_name
        pokestop.description = fort_description
        pokestop.image_url = fort_image

    else:
        gym = session.query(Gym).get(fort_id)

        gym.name = fort_name
        gym.description = fort_description
        gym.image_url = fort_image

    session.commit()
    session.flush()

def parse_pokemon_cell(cell, session):
    count_pokemons = 0

    for p in cell.get('wild_pokemons', []):

        # fix
        if int(p['time_till_hidden_ms']) < 0:
            p['time_till_hidden_ms'] = 300

        pokemon_spawnpoint = PokemonSpawnpoint()

        pokemon_spawnpoint.id = p['spawnpoint_id']
        pokemon_spawnpoint.cd_encounter = p['encounter_id']
        pokemon_spawnpoint.cd_pokemon = p['pokemon_data']['pokemon_id']

        pokemon_spawnpoint.latitude = p['latitude']
        pokemon_spawnpoint.longitude = p['longitude']
        pokemon_spawnpoint.date_till_hidden = p['time_till_hidden_ms'] / 1000.0
        pokemon_spawnpoint.date_disappear = datetime.fromtimestamp(
                (p['last_modified_timestamp_ms'] +
                 p['time_till_hidden_ms']) / 1000.0)
        pokemon_spawnpoint.date_change = datetime.fromtimestamp((p['last_modified_timestamp_ms']/1000))

        try:
            count_pokemons += 1

            session.merge(pokemon_spawnpoint)
            session.commit()
        finally:
            session.flush()

    return count_pokemons

def parse_pokestop(f, session):
    if 'lure_info' in f:
        lure_expiration = datetime.fromtimestamp(
            f['lure_info']['lure_expires_timestamp_ms'] / 1000.0)
    else:
        lure_expiration = None
    pokestop = Pokestop()

    pokestop.id = f['id']
    pokestop.is_enabled = f['enabled']
    pokestop.latitude = f['latitude']
    pokestop.longitude = f['longitude']

    pokestop.date_modified=datetime.fromtimestamp(f['last_modified_timestamp_ms'] / 1000.0)
    pokestop.date_lure_expiration = lure_expiration

    try:
        session.merge(pokestop)
        session.commit()
    finally:
        session.flush()

    return 1

def parse_gym(f, session):
    gym = Gym()

    gym.id = f['id']

    if not "owned_by_team" in f:
        gym.cd_guard_pokemon = 0
        gym.cd_team = 0
        gym.prestige = 0
    else:
        gym.cd_team = f['owned_by_team']
        gym.cd_guard_pokemon = f['guard_pokemon_id']
        gym.prestige = f['gym_points']
        # is_in_battle
    gym.is_enabled = f['enabled']
    gym.latitude = f['latitude']
    gym.longitude = f['longitude']
    gym.date_modified = datetime.fromtimestamp(f['last_modified_timestamp_ms'] / 1000.0)

    try:
        session.merge(gym)
        session.commit()
    finally:
        session.flush()

    return 1