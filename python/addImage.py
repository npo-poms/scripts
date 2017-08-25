#!/usr/bin/env python3
"""Script to add a image to all members of a group."""

from npoapi import MediaBackend, MediaBackendUtil as MU
import npoapi.xml.mediaupdate
from xml.dom import minidom

api = MediaBackend().command_line_client()
api.add_argument('mid',   type=str, nargs=1, help='The mid  of the object to handle')
api.add_argument('image', type=str, nargs='+', help='New image. If more than one is provided, they will be used alternately')
api.add_argument('title', type=str, nargs='?', help='title for new images')
api.add_argument('--only_if_none', action='store_true', default=False, help='Only if no images present yet')
api.add_argument('--dry_run', action='store_true', default=False, help='Dry run')
api.add_argument('--filter', type=str,  help="""
Filter. A piece of python code to filter. E.g. "memberType == npoapi.xml.mediaupdate.programUpdateType" or "member.type == 'PROMO'"
""")
api.add_argument('--to_object', action='store_true', default=False, help='Add to object itself too')
api.add_argument('--to_object_only', action='store_true', default=False, help='Add to object itself only')
api.add_argument('--max', type=int, nargs='?', help='Maximum number of objects to process')
api.add_argument('--max_query', type=int, nargs='?', help='Maximum number of objects to find')
api.add_argument('--segments', action='store_true', default=False, help='')

MU.logger = api.logger
args = api.parse_args()

mid = args.mid[0]
images = args.image
title = args.title
mediaUpdate = api.get_object(mid, ignore_not_found=True)
only_if_none = args.only_if_none
filter = args.filter
if args.dry_run:
    api.logger.info("Dry running")

count = 0

if mediaUpdate:
    if (args.to_object or args.to_object_only) and not args.dry_run:
        if not only_if_none or len(mediaUpdate.images.image) == 0:
            if title is None:
                title = mediaUpdate.title[0].value()
            api.logger.info("Adding image %s to %s", images[count % len(images)],  mid)
            api.add_image(mid, MU.create_image(images[count % len(images)], title=title))
            count += 1

    if not args.to_object_only:
        mediaType = type(mediaUpdate)
        members = []

        MU.descendants(api, mid, batch=200, target=members, log_progress=True, episodes=(mediaType == npoapi.xml.mediaupdate.groupUpdateType), segments=args.segments,  limit=args.max_query)
        api.logger.info("Found %s members in %s", len(members), mid)
        for idx, member in enumerate(MU.iterate_objects(members)):
            member_mid = member.mid
            memberType = type(member)
            if filter:
                result = eval(filter)
                api.logger.debug("Execed %s result %s", str(filter), str(result))
                if not result:
                    api.logger.info("Skipping %s, %s %s because of filter %s", str(memberType), str(member.type), member_mid, filter)
                    continue

            if title is None:
                t = member.title[0].value()
            else:
                t = title
            if not only_if_none or len(member.images.image) == 0:
                api.logger.info("%s/%s Adding image %s to %s", idx, len(members), images[count % len(images)], member_mid)
                count += 1
                if not args.dry_run:
                    image = MU.create_image(images[count % len(images)], title=t)
                    api.add_image(member_mid, image)
                if args.max and count >= args.max:
                    break

            else:
                api.logger.info("%s/%s Not adding image to %s because it has %s already", idx, len(members), member_mid, len(member.images.image))


else:
    api.logger.info("Not found %s" % mid)

api.logger.info("Added %s images" % str(count))

