#!/usr/bin/env python
from npoapi import MediaBackend, MediaBackendUtil as MU
import csv
import os

""""
Reads a CSV with three columns
"""

api = MediaBackend().command_line_client()
log = api.logger

log.info(str(api))

rows = []

with open(os.getenv("HOME") + '/Downloads/zappechtgebeurd-kinderen-edited.csv', mode='r', encoding='utf-8',  errors='ignore') as file:
    reader = csv.reader(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    i = 0
    for row in reader:
        i = i + 1
        log.info("line %s", str(i))
        rows.append(row)


for row in rows:
    mid = row[0]
    title = row[1]
    episode = row[2]
    log.info("MID %s", mid)
    existing = api.get_object(mid)
    if existing:
        try:
            existing_title = MU.main_title(existing)
            existing_episode = MU.title(existing, 'SUB')
            if episode.__eq__(""):
                episode = None
            if title != existing_title or episode != existing_episode:
                log.info("updating: %s -> %s/ %s -> %s", existing_title, title, existing_episode, episode)
                MU.main_title(existing, title)
                MU.title(existing, 'SUB', episode)
                log.info("%s", MU.main_title(existing))
                MU.clear_invalid_image_fields(existing)
                api.post(existing)
            else:
                log.info("existing: %s: %s", title, episode)
        except BaseException as e:
            log.error(e, exc_info=True)



