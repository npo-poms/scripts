#!/usr/bin/env python3
"""
This script checks wether a poms playlist contains multiple translations of the same source. If so, it will delete remove all but one.
"""
from npoapi import MediaBackend

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
args = api.parse_args()

group = args.mid[0]
members = api.members(group, max=3000, batch=50)

translations_for_mid = {}
for member in members:
    update = member.firstChild
    mid = update.attributes["mid"].value
    relations = member.getElementsByTagName("relation")
    for relation in relations:
        relation_type = relation.attributes["type"].value
        if relation_type == "TRANSLATION_SOURCE":
            translation_source = relation.firstChild.nodeValue
            if not translation_source in translations_for_mid:
                translations_for_mid[translation_source] = []
            translations_for_mid[translation_source].append(mid)

#print(pprint.pformat(map))
for mid in translations_for_mid:
    mid_to_delete = sorted(translations_for_mid[mid])[1:]
    if len(mid_to_delete) > 0:
        print("for %s are the following translations %s , to delete are %s" % (mid, str(translations_for_mid[mid]), str(mid_to_delete)))
        for d in mid_to_delete:
            print("Deleting %s from %s" % (d, group))
            api.delete_member(d, group)



