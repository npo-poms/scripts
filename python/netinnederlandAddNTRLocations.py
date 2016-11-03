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
    location = member.locations.location[0]
    programUrl = location.programUrl
    publishStart = location.publishStart
    publishStop = location.publishStop
    crids = member.crids
    print(member)

