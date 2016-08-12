#!/usr/local/bin/python2.6
# -*- coding: utf-8 -*-
import urllib
import urllib2
import re
import os
import sys
import time
import cookielib
#import smtplib
import random

#from datetime import datetime, date, time, timedelta
#from xml.dom import minidom

class PtcUserRegister:
    """Класс для голосования на megafashion.ru"""
    def __init__(self, index):
        self.index = index

        self.siteCookie=cookielib.CookieJar()
        self.siteOpener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.siteCookie), urllib2.HTTPHandler())
        self.siteHeaders =  {
            'User-agent' : 'Mozilla/5.0 (Macintosh; Fucking Team Killer) AppleWebKit/537.78.2 (KHTML, like Gecko) Version/7.0.6 Safari/537.78.2',
        }


    def reg(self):
        requestURL = "https://club.pokemon.com/us/pokemon-trainer-club/sign-up/"
        requestData = urllib.urlencode({
            'csrfmiddlewaretoken':'ldfegppEBxNQ23By7oMbeuazu4rslaro',
            'dob': '1988-07-02',
            'country': 'RU'
        })

        requestQuery = self.siteOpener.open(urllib2.Request(requestURL, requestData, self.siteHeaders))
        requestResponse = requestQuery.read()
        print requestResponse


if __name__ == "__main__":
    ptc = PtcUserRegister(9)
    ptc.reg()

