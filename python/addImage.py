#!/usr/bin/env python3
"""Script to add a image to all members of a group."""

from npoapi import MediaBackend
from npoapi.xml import mediaupdate
from npoapi.xml import poms

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
api.add_argument('image', type=str, nargs=1, help='new image')
api.add_argument('title', type=str, nargs='?', help='new image')

args = api.parse_args()

mid = args.mid[0]
image = args.image[0]
title = args.title
bytes = api.get(mid, ignore_not_found=True)
if bytes:
    members = api.members(mid, batch=200)
    members.extend(api.episodes(mid, batch=200))

    for member in map(lambda m: poms.CreateFromDOM(m.getElementsByTagName("mediaUpdate")[0], mediaupdate.Namespace),
                      members):
        member_mid = member.mid
        print("Adding image " + image + " to " + member_mid)
        if title is None:
            t = member.title[0].value()
        else:
            t = title
        api.add_image(member_mid, image, title=t)
else:
    print("Not found %s", mid)



