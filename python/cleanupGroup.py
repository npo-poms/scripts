#!/usr/bin/env python3
"""
This script checks wether a poms playlist contains multiple translations of the same source. If so, it will delete remove all but one.
"""
from npoapi import MediaBackend

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
args = api.parse_args()

group = args.mid[0]
members = api.members(group, batch=200, log_progress=True)

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
    sorted_mids = sorted(translations_for_mid[mid])
    mids_to_delete = sorted_mids[1:]
    mid_to_keep = sorted_mids[0]
    if len(mids_to_delete) > 0:
        print("for %s are the following translations %s , to delete are %s" % (mid, str(translations_for_mid[mid]), str(mids_to_delete)))
        for d in mids_to_delete:
            print("Deleting %s from %s (keeping %s)" % (d, group, mid_to_keep))
            api.delete_member(d, group)



