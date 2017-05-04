#!/usr/bin/env python3
"""Script to add a image to all members of a group."""

from npoapi import MediaBackend, MediaBackendUtil as MU
from npoapi.xml import mediaupdate
from npoapi.xml import poms

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
api.add_argument('group', type=str, nargs=1, help='Group')
api.add_argument('--use_get', action='store_true', default=False)
api.add_argument('--position', type=int, default=None)

args = api.parse_args()

mid   = args.mid[0]
group = args.group[0]

if args.use_get:
    media = poms.CreateFromDocument(api.get(mid))
    memberOf = mediaupdate.memberRef(group)
    memberOf.highlighted = False
    memberOf.position = args.position
    media.memberOf.append(memberOf)

    api.post(media)
else:
    api.add_member(mid, group, position=args.position)







