#!/usr/bin/env python
from npoapi import MediaBackend, MediaBackendUtil as MU
import csv

api = MediaBackend().command_line_client()
log = api.logger


with open('/Users/michiel/Downloads/zappechtgebeurd-kinderen-edited.csv', mode='r', encoding='utf-8') as file:
    reader = csv.reader(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for row in reader:
        mid = row[0]
        title = row[1]
        episode = row[2]
        existing = api.get_object(mid)
        new_title = MU.main_title(existing)
        new_episode = MU.title(existing, 'SUB')
        if title != new_title or episode != new_episode:
            log.info("updating: %s -> %s: %s -> %s", title, new_title, episode, new_episode)
            MU.main_title(existing, new_title)
            MU.title(existing, 'SUB', new_episode)
            api.post(existing)
        else:
            log.info("existing: %s: %s", title, episode)


