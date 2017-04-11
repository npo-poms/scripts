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
    print(image_type)
    MU.set_image_fields(new_image, title=image_title, source=image_source, source_name=image_source_name, credits=image_credits, image_type=image_type)

    member.images.image.append(new_image)



def filter_image(member, ids):
    return type(member) == programUpdateType


if __name__ == "__main__":
    for_all_descendants.init(add_image, filter_image)
    for_all_descendants.api.add_argument("image_file", type=str, nargs=1, help='image file name')
    for_all_descendants.api.add_argument("image_title", type=str, nargs=1, help='image title')
    for_all_descendants.api.add_argument("--image_credits", type=str, help='image credits')
    for_all_descendants.api.add_argument("--image_source_name", type=str,  help='image source name')
    for_all_descendants.api.add_argument("--image_source", type=str, help='image source')
    for_all_descendants.api.add_argument("--image_type", type=str, help='image type')

    args = for_all_descendants.api.parse_args()
    global image_file
    image_file = args.image_file[0]
    global image_title
    image_title = args.image_title[0]
    global image_credits
    image_credits = args.image_credits
    print(image_credits)
    global image_source_name
    image_source_name = args.image_source_name
    global image_source
    image_source = args.image_source
    global image_type
    image_type = args.image_type

    for_all_descendants.main(add_image, filter_image)



