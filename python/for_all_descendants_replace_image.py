#!/usr/bin/env python3
from npoapi.xml.mediaupdate import programUpdateType

import for_all_descendants
import datetime
from npoapi import MediaBackendUtil as MU

NOW = datetime.datetime.utcnow()


def add_image(member, idx):
    new_image = None
    for image in member.images.image:
        if image.title[0] != image_title:
            image.publishStop = NOW
        else:
            new_image = image
    if not new_image:
        new_image = MU.create_image(image_file)

    MU.set_image_fields(new_image, title=image_title, source="http://www.vpro.nl/nooitmeerslapen.html", source_name="VPRO", credits="VPRO", image_type="LOGO")

    member.images.image.append(new_image)



def filter_image(member, ids):
    return type(member) == programUpdateType


if __name__ == "__main__":
    for_all_descendants.init(add_image, filter_image)
    for_all_descendants.api.add_argument("image_file", type=str, nargs=1, help='image file name')
    for_all_descendants.api.add_argument("image_title", type=str, nargs=1, help='image title')

    global image_file
    image_file = for_all_descendants.api.parse_args().image_file[0]
    global image_title
    image_title = for_all_descendants.api.parse_args().image_title[0]


    for_all_descendants.main(add_image, filter_image)



