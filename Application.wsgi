#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os

path="/home/apache/org-tatarnikov-pokestats/.python"

sys.path.insert(0, path)
os.chdir(path)

from Application import application as application

import sys
sys.stdout = sys.stderr