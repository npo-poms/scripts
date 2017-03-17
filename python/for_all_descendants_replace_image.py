#!/usr/bin/env python3
from npoapi.xml.mediaupdate import programUpdateType

import for_all_descendants
import datetime
from npoapi import MediaBackend, MediaBackendUtil as MU
import sys

NOW = datetime.datetime.utcnow()

imageFile = sys.argv[2]

def add_image(member, idx):
    for image in member.images.image:
        image.publishStop = NOW
    title = member.title[0].value()
    new_image = MU.create_image(imageFile, title=title)
    member.images.image.append(new_image)
    member.validateBinding()
    print(MU.toxml(member))

def filter_image(member, ids):
    return type(member) == programUpdateType


if __name__ == "__main__":
    process = "print"
    for_all_descendants.main(add_image, filter_image)



