#!/usr/bin/env python3

from npoapi import MediaBackend
from mediaupdate import MediaUpdate
import pprint

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
args = api.parse_args()

mid = args.mid[0]


print(pprint.pformat(MediaUpdate.CreateFromDOM(api.get(mid))))


