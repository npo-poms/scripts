#!/usr/bin/env python3
""" """
"""Script to add a location """

from npoapi import MediaBackend, MediaBackendUtil as MU
import requests
import pickle
import os.path

api = MediaBackend().command_line_client()
api.add_argument('mid', type=str, nargs=1, help='The mid  of the object to handle')

args = api.parse_args()


filename = "/tmp/members.pkl"

if os.path.isfile(filename):
    with open(filename, 'rb') as input:
        members = pickle.load(input)
else:
    members = []
    MU.descendants(api, args.mid[0], batch=200, target=members, log_progress=True)
    with open(filename, 'wb') as output:
        pickle.dump(members, output, pickle.HIGHEST_PROTOCOL)
        api.logger.info("Wrote %s", filename)
count_new = 0
count_done = 0
count_404 = 0

for member in MU.iterate_objects(members):
    print("%s %s %s " % (member.mid, member.locations.location[0].programUrl, str(list(member.crid))), end="")
    has_mp4 = False
    if len(member.locations.location) >= 1:
        for location in member.locations.location:
            if location.avAttributes.avFileFormat == 'MP4':
                has_mp4 = True
        for location in member.locations.location:
            if location.avAttributes.avFileFormat == 'HASP':
                programUrl = location.programUrl
                publishStart = location.publishStart
                publishStop = location.publishStop
                last_part = programUrl.split('/')[-1]
                new_program_url = 'http://video.omroep.nl/ntr/schooltv/beeldbank/video/' + last_part + ".mp4"
                resp = requests.head(new_program_url)
                new_location = MU.create_location(new_program_url, embargo={'publish_start':publishStart, 'publish_stop':publishStop}, avFileFormat='MP4')
                print("%s %s" % (new_program_url, resp.status_code), end="")
                if not has_mp4:
                    if resp.status_code == 302:
                        #print(api.add_location(member.mid, new_location))
                        count_new += 1
                    else:
                        count_404 += 1
                else:
                    count_done += 1


    print()
print("new locations: %s, not added because 404: %s, already had mp4: %s" % (str(count_new, count_404, count_done)))

