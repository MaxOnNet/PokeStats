#!/usr/bin/python
# -*- coding: utf-8 -*-

from Reports import config
from Reports.Map import Map

from flask_compress import Compress

application = Map(__name__)
Compress(application)
config['ROOT_PATH'] = application.root_path

if __name__ == '__main__':
    application.run(threaded=True, host="127.0.0.1", port="5000")