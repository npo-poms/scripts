#!/usr/bin/env python3
"""
 
"""

import datetime
import json
from npoapi import Schedule
from npoapi import MediaBackend
from npoapi import Binding
from npoapi.data import TextualTypeEnum


client = Schedule(env="prod").configured_login()
backend = MediaBackend(env="prod").configured_login()

channels = ['NED1', 'NED2', 'NED3','RAD1', 'RAD2', 'RAD3', 'RAD4', 'FUNX']
#channels = ['RAD3']
print(client.url)
print(backend.url)


day = datetime.date(2022, 12, 1)
end = datetime.date(2023, 1, 6)
while day < end:
 
 
    for channel in channels:
        print(day, channel)
        resp = client.get(guideDay=day, channel=channel, properties="titles")
        result = json.loads(resp)
        items = result.get("items")
        for item in items:
            media = item.get("media")
            mid = media.get("mid")
            titles = media.get("titles")
            main_title = next(filter(lambda t: t.get("type") == 'MAIN', titles), None)
            if main_title:
                #print(channel, str(day), mid, main_title.get("value"))
                pass
            else:
                print(channel, str(day), mid, "NO TITLE")
                full = backend.get_full_object(mid, binding=Binding.XSDATA)
                first_title = full.title[0]
                if first_title.type == TextualTypeEnum.MAIN:
                    print("Title expected to be", first_title.value)
                else:
                    print("OOOOODDD")
                
    day  += datetime.timedelta(days=1)

