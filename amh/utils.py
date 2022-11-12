# -*- coding: utf-8 -*-
""" Utility functions"""

import configparser
import unidecode

def readConfig():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config

def clean_slot(slot):
    slot = slot.lower()  # Lower case
    slot = unidecode.unidecode(slot)  # unasccented string
    return slot    