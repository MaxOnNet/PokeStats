#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time

def analyticts_timer(f):
    def tmp(*args, **kwargs):
        t = time.time()
        res = f(*args, **kwargs)
        print "Время выполнения функции: %f" % (time.time()-t)
        return res

    return tmp
