#!/usr/bin/env python3

from npoapi import MediaBackend
import pprint

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
args = api.parse_args()

group = args.mid[0]
members = api.members(group, max=3000, batch=50)

map = {}
for member in members:
    update = member.firstChild
    mid = update.attributes["mid"].value
    relations = member.getElementsByTagName("relation")
    for relation in relations:
        type = relation.attributes["type"].value
        if type == "TRANSLATION_SOURCE":
            translation_source = relation.firstChild.nodeValue
            if not translation_source in map:
                map[translation_source] = []
            map[translation_source].append(mid)

#print(pprint.pformat(map))
for mid in map:
    todelete = sorted(map[mid])[1:]
    if len(todelete) > 0:
        print("for %s are the following translations %s , to delete are %s" %  (mid, str(map[mid]), str(todelete)))
        for d in todelete:
            print("Deleting %s from %s" % (d, group))
            api.delete_member(d, group)



