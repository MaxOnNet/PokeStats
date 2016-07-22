#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ColumnDefault, Float, BigInteger
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func, select
from sqlalchemy.orm import relationship
from sqlalchemy.orm import object_session

from sqlalchemy_utils import URLType, CountryType, PhoneNumberType, UUIDType, IPAddressType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from datetime import datetime
from base64 import b64encode

log = logging.getLogger(__name__)
Base = declarative_base()

class Pokemon(Base):
    __tablename__ = 'pokemon'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(Integer(), primary_key=True, autoincrement=True, doc="")

    name = Column(String(64), nullable=False, doc="")


class PokemonSpawnpoint(Base):
    __tablename__ = 'pokemon_spawnpoint'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(BigInteger(), doc="")
    cd_encounter = Column(BigInteger(), primary_key=True, doc="")
    cd_pokemon = Column(Integer(), ForeignKey('pokemon.id'), nullable=False, doc="")

    latitude = Column(Float())
    longitude = Column(Float())
    date_disappear = Column(DateTime(), nullable=False, default=func.utc_timestamp())

    date_create = Column(DateTime(), nullable=False, default=func.utc_timestamp())
    date_change = Column(DateTime(), nullable=False, default=func.utc_timestamp(), onupdate=func.utc_timestamp())

    pokemon = relationship("Pokemon", backref="PokemonSpawnpoint")

    @classmethod
    def get_active(cls, session):
        return session.query(PokemonSpawnpoint).filter(PokemonSpawnpoint.date_disappear > datetime.now())


class Pokestop(Base):
    __tablename__ = 'pokestop'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8', 'mysql_collate': 'utf8_general_ci',
                      'mysql_comment': ''}

    id = Column(BigInteger(), primary_key=True, doc="")

    is_enabled = Column(Boolean())

    latitude = Column(Float())
    longitude = Column(Float())

    date_modified = Column(DateTime(), nullable=True)
    date_lure_expiration = Column(DateTime(), nullable=True)

    date_create = Column(DateTime(), nullable=False, default=func.utc_timestamp())
    date_change = Column(DateTime(), nullable=False, default=func.utc_timestamp(), onupdate=func.utc_timestamp())


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

    id = Column(BigInteger(), primary_key=True, doc="")
    cd_team = Column(Integer(), ForeignKey('team.id'), nullable=False, doc="")
    cd_guard_pokemon = Column(Integer(), ForeignKey('pokemon.id'), nullable=False, doc="")

    is_enabled = Column(Boolean())

    latitude = Column(Float())
    longitude = Column(Float())

    date_modified = Column(DateTime(), nullable=True)
    date_create = Column(DateTime(), nullable=False, default=func.utc_timestamp())
    date_change = Column(DateTime(), nullable=False, default=func.utc_timestamp(), onupdate=func.utc_timestamp())


def parse_map(map_dict, session):
    cells = map_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    for cell in cells:
        for p in cell.get('wild_pokemons', []):
            pokemon_spawnpoint = PokemonSpawnpoint()

            pokemon_spawnpoint.id = p['spawnpoint_id']
            pokemon_spawnpoint.cd_encounter = p['encounter_id']
            pokemon_spawnpoint.cd_pokemon = p['pokemon_data']['pokemon_id']

            pokemon_spawnpoint.latitude = p['latitude']
            pokemon_spawnpoint.longitude = p['longitude']

            pokemon_spawnpoint.date_disappear = datetime.fromtimestamp(
                    (p['last_modified_timestamp_ms'] +
                     p['time_till_hidden_ms']) / 1000.0)

            session.merge(pokemon_spawnpoint)

        for f in cell.get('forts', []):
            if f.get('type') == 1:  # Pokestops
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

                pokestop.date_modified =datetime.fromtimestamp(f['last_modified_timestamp_ms'] / 1000.0)
                pokestop.date_lure_expiration = lure_expiration

                session.merge(pokestop)

            else:  # Currently, there are only stops and gyms
                gym = Gym()
                gym.id = f['id']
                gym.cd_team = f['owned_by_team']
                gym.cd_guard_pokemon = f['guard_pokemon_id']
                gym.is_enabled = f['enabled']
                gym.latitude = f['latitude']
                gym.longitude = f['longitude']
                gym.date_modified = datetime.fromtimestamp(f['last_modified_timestamp_ms'] / 1000.0)

                session.merge(gym)

    session.flush()
