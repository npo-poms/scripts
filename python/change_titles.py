#!/usr/bin/env python
from npoapi import MediaBackend, MediaBackendUtil as MU
import csv
import os

api = MediaBackend().command_line_client()
log = api.logger

log.info(str(api))

with open(os.getenv("HOME") + '/Downloads/zappechtgebeurd-kinderen-edited.csv', mode='r', encoding='utf-8') as file:
    reader = csv.reader(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for row in reader:
        mid = row[0]
        title = row[1]
        episode = row[2]
        log.info("MID %s", mid)
        existing = api.get_object(mid)
        if existing:
            existing_title = MU.main_title(existing)
            existing_episode = MU.title(existing, 'SUB')
            if title != existing_title or episode != existing_episode:
                log.info("updating: %s -> %s: %s -> %s", existing_title, title, existing_episode, episode)
                MU.main_title(existing, title)
                MU.title(existing, 'SUB', episode)
                log.info("%s", MU.main_title(existing))
                api.post(existing)
            else:
                log.info("existing: %s: %s", title, episode)


