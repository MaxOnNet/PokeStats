# -*- coding: utf-8 -*-

import struct
from math import cos, asin, sqrt


def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * \
        cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a)) * 1000


def convert(distance, from_unit, to_unit):  # Converts units
    # Example of converting distance from meters to feet:
    # convert(100.0,"m","ft")
    conversions = {
        "mm": {"mm": 1.0,
               "cm": 1.0 / 10.0,
               "m": 1.0 / 1000.0,
               "km": 1.0 / 1000000,
               "ft": 0.00328084,
               "yd": 0.00109361,
               "mi": 1.0 / 1609340.0007802},
        "cm": {"mm": 10.0,
               "cm": 1.0,
               "m": 1.0 / 100,
               "km": 1.0 / 100000,
               "ft": 0.0328084,
               "yd": 0.0109361,
               "mi": 1.0 / 160934.0},
        "m": {"mm": 1000,
              "cm": 100.0,
              "m": 1.0,
              "km": 1.0 / 1000.0,
              "ft": 3.28084,
              "yd": 1.09361,
              "mi": 1.0 / 1609.34},
        "km": {"mm": 100000,
               "cm": 10000.0,
               "m": 1000.0,
               "km": 1.0,
               "ft": 3280.84,
               "yd": 1093.61,
               "mi": 1.0 / 1.60934},
        "ft": {"mm": 1.0 / 328.084,
               "cm": 1.0 / 32.8084,
               "m": 1.0 / 3.28084,
               "km": 1 / 3280.84,
               "ft": 1.0,
               "yd": 1.0 / 3.0,
               "mi": 1.0 / 5280.0},
        "yd": {"mm": 1.0 / 328.084,
               "cm": 1.0 / 32.8084,
               "m": 1.0 / 3.28084,
               "km": 1 / 1093.61,
               "ft": 3.0,
               "yd": 1.0,
               "mi": 1.0 / 1760.0},
        "mi": {"mm": 1609340.0007802,
               "cm": 160934.0,
               "m": 1609.34,
               "km": 1.60934,
               "ft": 5280.0,
               "yd": 1760.0,
               "mi": 1.0}
    }
    return distance * conversions[from_unit][to_unit]


def dist_to_str(distance, unit):
    return '{:.2f}{}'.format(distance, unit)


def format_dist(distance, unit="m"):
    # Assumes that distance is in meters and converts it to the given unit, then a formatted string is returned
    # Ex: format_dist(1500, 'km') returns the string "1.5km"
    return dist_to_str(convert(distance, 'm', unit), unit)


def format_time(seconds):
    # Return a string displaying the time given as seconds or minutes
    if seconds <= 0.0:
        return '{:.2f} seconds'.format(seconds)
    elif seconds <= 1.0:
        return '{:.2f} second'.format(seconds)
    elif seconds < 60:
        return '{:.2f} seconds'.format(seconds)
    elif seconds > 60 and seconds < 3600:
        minutes = seconds / 60
        return '{:.2f} minutes'.format(minutes)
    return '{:.2f} seconds'.format(seconds)


def i2f(int):
    return struct.unpack('<d', struct.pack('<Q', int))[0]


def print_green(message):
    print(u'\033[92m' + message.decode('utf-8') + '\033[0m')


def print_yellow(message):
    print(u'\033[93m' + message.decode('utf-8') + '\033[0m')


def print_red(message):
    print(u'\033[91m' + message.decode('utf-8') + '\033[0m')


'''Provides utility functions for encoding and decoding linestrings using the
Google encoded polyline algorithm.
'''

def encode_coords(coords):
    '''Encodes a polyline using Google's polyline algorithm

    See http://code.google.com/apis/maps/documentation/polylinealgorithm.html
    for more information.

    :param coords: Coordinates to transform (list of tuples in order: latitude,
    longitude).
    :type coords: list
    :returns: Google-encoded polyline string.
    :rtype: string
    '''

    result = []

    prev_lat = 0
    prev_lng = 0

    for coord in coords:
        lat, lng = int(coord['lat'] * 1e5), int(coord['lng'] * 1e5)

        d_lat = _encode_value(lat - prev_lat)
        d_lng = _encode_value(lng - prev_lng)

        prev_lat, prev_lng = lat, lng

        result.append(d_lat)
        result.append(d_lng)

    return ''.join(c for r in result for c in r)

def _split_into_chunks(value):
    while value >= 32: #2^5, while there are at least 5 bits

        # first & with 2^5-1, zeros out all the bits other than the first five
        # then OR with 0x20 if another bit chunk follows
        yield (value & 31) | 0x20
        value >>= 5
    yield value

def _encode_value(value):
    # Step 2 & 4
    value = ~(value << 1) if value < 0 else (value << 1)

    # Step 5 - 8
    chunks = _split_into_chunks(value)

    # Step 9-10
    return (chr(chunk + 63) for chunk in chunks)


def decode(point_str):
    '''Decodes a polyline that has been encoded using Google's algorithm
    http://code.google.com/apis/maps/documentation/polylinealgorithm.html

    This is a generic method that returns a list of (latitude, longitude)
    tuples.

    :param point_str: Encoded polyline string.
    :type point_str: string
    :returns: List of 2-tuples where each tuple is (latitude, longitude)
    :rtype: list

    '''

    # sone coordinate offset is represented by 4 to 5 binary chunks
    coord_chunks = [[]]
    for char in point_str:

        # convert each character to decimal from ascii
        value = ord(char) - 63

        # values that have a chunk following have an extra 1 on the left
        split_after = not (value & 0x20)
        value &= 0x1F

        coord_chunks[-1].append(value)

        if split_after:
                coord_chunks.append([])

    del coord_chunks[-1]

    coords = []

    for coord_chunk in coord_chunks:
        coord = 0

        for i, chunk in enumerate(coord_chunk):
            coord |= chunk << (i * 5)

        #there is a 1 on the right if the coord is negative
        if coord & 0x1:
            coord = ~coord #invert
        coord >>= 1
        coord /= 100000.0

        coords.append(coord)

    # convert the 1 dimensional list to a 2 dimensional list and offsets to
    # actual values
    points = []
    prev_x = 0
    prev_y = 0
    for i in xrange(0, len(coords) - 1, 2):
        if coords[i] == 0 and coords[i + 1] == 0:
            continue

        prev_x += coords[i + 1]
        prev_y += coords[i]
        # a round to 6 digits ensures that the floats are the same as when
        # they were encoded
        points.append((round(prev_x, 6), round(prev_y, 6)))

    return points