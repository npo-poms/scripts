#!/usr/bin/env python3
""" """
from npoapi import MediaBackend
from npoapi.xml import mediaupdate

poms = MediaBackend().command_line_client()
poms.add_argument('mid', type=str, nargs=1, help='The mid  of the object to get')
poms.add_argument('duration', type=str, nargs=1, help='The duration to set')

args = poms.parse_args()
bytes = poms.get(args.mid[0])
update = mediaupdate.CreateFromDocument(bytes)
duration = args.duration[0]
update.duration = duration
poms.post(update)
