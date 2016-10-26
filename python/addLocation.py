#!/usr/bin/env python3
""" """
"""Script to add a location """

from npoapi import MediaBackend, MediaBackendUtil as MU

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')
api.add_argument('location', type=str, nargs=1, help='URL of the new "location"')

args = api.parse_args()

print(api.add_location(args.mid[0], MU.create_location(args.location[0])))

