#!/usr/bin/env python3
"""Script to add a genre to all members of a group. Supported in poms >= 3.2 only"""
import sys

from npoapi import MediaBackend
from npoapi.xml import mediaupdate
from npoapi.xml import poms

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
api.add_argument('genre', type=str, nargs=1, help='new Genre')
args = api.parse_args()

genre_id = args.genre[0]

bytes = api.get(args.mid[0], ignore_not_found=True)
if bytes:
    object = poms.CreateFromDocument(bytes)
    if type(object) == mediaupdate.programUpdateType:
        object.genre.append(genre_id)
        api.post(object)

    members = api.members(args.mid[0], batch=200)

    for member in map(lambda m: poms.CreateFromDOM(m.getElementsByTagName("mediaUpdate")[0], mediaupdate.Namespace), members):
        member_mid = member.mid
        print("Adding genre " + genre_id + " to " + member_mid)
        member.genre.append(genre_id)
        api.post(member)


