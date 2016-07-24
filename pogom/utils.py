#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import getpass
import argparse
import re
import uuid
import os
import json
from datetime import datetime, timedelta

from . import config
from exceptions import APIKeyException


def parse_unicode(bytestring):
    decoded_string = bytestring.decode(sys.getfilesystemencoding())
    return decoded_string


def insert_mock_data(location, num_pokemons):
    from .models import Pokemon
    from .search import generate_location_steps

    prog = re.compile("^(\-?\d+\.\d+)?,\s*(\-?\d+\.\d+?)$")
    res = prog.match(location)
    latitude, longitude = float(res.group(1)), float(res.group(2))

    locations = [l for l in generate_location_steps((latitude, longitude), num_pokemons)]
    disappear_time = datetime.now() + timedelta(hours=1)

    for i in xrange(num_pokemons):
        Pokemon.create(encounter_id=uuid.uuid4(),
                       spawnpoint_id='sp{}'.format(i),
                       pokemon_id=(i+1) % 150,
                       latitude=locations[i][0],
                       longitude=locations[i][1],
                       disappear_time=disappear_time)


def get_pokemon_name(pokemon_id):
    if not hasattr(get_pokemon_name, 'names'):
        file_path = os.path.join(
            config['ROOT_PATH'],
            config['LOCALES_DIR'],
            'pokemon.{}.json'.format(config['LOCALE']))

        with open(file_path, 'r') as f:
            get_pokemon_name.names = json.loads(f.read())

    return get_pokemon_name.names[str(pokemon_id)]

