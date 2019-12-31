#!/usr/bin/python
from configparser import ConfigParser
import os

def db_config(filename='~/conf/database.ini', section='postgresql-test'):

    parser = ConfigParser()
    fullpath = os.path.expanduser(filename)
    parser.read(fullpath)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception("Section "+section+" not found in the "+filename+" file")

    return db