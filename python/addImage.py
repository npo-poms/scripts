#!/usr/bin/env python3
"""Script to add a image to all members of a group."""

from npoapi import MediaBackend, MediaBackendUtil as MU
import npoapi.xml.mediaupdate
from xml.dom import minidom

api = MediaBackend().command_line_client()
api.add_argument('mid',   type=str, nargs=1, help='The mid  of the object to handle')
api.add_argument('image', type=str, nargs=1, help='new image')
api.add_argument('title', type=str, nargs='?', help='title for new images')
api.add_argument('--only_if_none', action='store_true', default=False, help='Only if no images present yet')
api.add_argument('--dry_run', action='store_true', default=False, help='Dry run')
api.add_argument('--filter', type=str,  help='Filter. A piece of python code to filter')
api.add_argument('--to_object', action='store_true', default=False, help='Add to object itself too')
api.add_argument('--to_object_only', action='store_true', default=False, help='Add to object itself only')

MU.logger = api.logger
args = api.parse_args()

mid = args.mid[0]
image = args.image[0]
title = args.title
mediaUpdate = api.get_object(mid, ignore_not_found=True)
only_if_none = args.only_if_none
filter = args.filter
if args.dry_run:
    api.logger.info("Dry running")


if mediaUpdate:
    if (args.to_object or args.to_object_only) and not args.dry_run:
        if title is None:
            title = mediaUpdate.title[0].value()
        api.logger.info("Adding image to %s", mid)
        api.add_image(mid, MU.create_image(image, title=title))

    if not args.to_object_only:
        mediaType = type(mediaUpdate)
        members = []

        MU.descendants(api, mid, batch=200, target=members, log_progress=True, episodes=(mediaType == npoapi.xml.mediaupdate.groupUpdateType))
        api.logger.info("Found %s members in %s", len(members), mid)
        for idx, member in enumerate(MU.iterate_objects(members)):
            member_mid = member.mid
            full = api.get

            if filter:
                result = eval(filter)
                api.logger.debug("Execed %s result %s", str(filter), str(result))
                if not result:
                    api.logger.info("Skipping %s because of filter", member_mid)
                    continue

            if title is None:
                t = member.title[0].value()
            else:
                t = title
            if not only_if_none or len(member.images.image) == 0:
                api.logger.info("%s/%s Adding image to %s", idx, len(members), member_mid)
                if not args.dry_run:
                    api.add_image(member_mid, MU.create_image(image, title=t))
            else:
                api.logger.info("%s/%s Not adding image to %s because it has %s already", idx, len(members), member_mid, len(member.images.image))


else:
    print("Not found %s" % mid)



