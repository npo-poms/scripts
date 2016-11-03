#!/usr/bin/env python3
""" """
"""Script to add a location """

from npoapi import MediaBackend, MediaBackendUtil as MU

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')

args = api.parse_args()

members = []
MU.descendants(api,
               args.mid[0], batch=200, target=members, log_progress=True, limit=100)

for member in MU.iterate_objects(members):
    print("%s %s %s" % (member.mid, member.locations.location[0].programUrl, str(list(member.crid))))
    if len(member.locations.location) == 1:

        location = member.locations.location[0]
        if location.avAttributes.avFileFormat == 'HASP':
            programUrl = location.programUrl
            publishStart = location.publishStart
            publishStop = location.publishStop
            lastpart = programUrl.split('/')[-1]
            newLocation = 'http://video.omroep.nl/ntr/schooltv/beeldbank/video/' + lastpart + ".mp4"
            print(newLocation)

    #print(member)

