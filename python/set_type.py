#!/usr/bin/env python3
"""The generic tool  npo_mediabackend  will let you too must things. This is an example for how to make a more specific tool"""
from npoapi import MediaBackend
from npoapi.xml import mediaupdate, media
import sys

poms = MediaBackend().command_line_client()

poms.add_argument('id', type=str, nargs=1, help='The mid or crid of the object to handle')
poms.add_argument('type', type=str, nargs='?', help='The new type')
poms.add_argument('avType', type=str, nargs='?', help='The new avtype')

args = poms.parse_args()

id = args.id[0]

xml = poms.get(id, ignore_not_found=True)
if xml:
    object = mediaupdate.CreateFromDocument(xml)
    if args.type:
        if type(object) is mediaupdate.programUpdateType:
            object.type = getattr(media.programTypeEnum, args.type)
        elif type(object) is mediaupdate.groupUpdateType:
            object.type = getattr(media.groupTypeEnum, args.type)
    if args.avType:
        object.avType = getattr(media.avTypeEnum, args.avType)
    poms.post(object)
else:
    sys.stderr.write("The object %s is not found in poms")
