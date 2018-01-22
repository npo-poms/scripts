#!/usr/bin/env python3
from npoapi.xml.mediaupdate import programUpdateType

from for_all_descendants import ForAllDescendants
import datetime
from npoapi import MediaBackendUtil as MU

NOW = datetime.datetime.utcnow()

class ForAllDescendantsReplaceImage(ForAllDescendants):

    def __init__(self):
        super().__init__(processor = self.nope)
        self.description = "Replacing image"

    def command_line(self):
        super().command_line()
        self.api.add_argument("image_file", type=str, nargs=1, help='image file name')

        self.api.add_argument("image_title", type=str, nargs=1, help='image title')
        self.api.add_argument("--image_credits", type=str, help='image credits')
        self.api.add_argument("--image_source_name", type=str, help='image source name')
        self.api.add_argument("--image_source", type=str, help='image source')
        self.api.add_argument("--image_type", type=str, default='PICTURE', help='image type')

    def parse_args(self):
        super().parse_args()
        args = self.api.parse_args()
        self.image_file = args.image_file[0]
        self.image_title = args.image_title[0]

        self.image_credits = args.image_credits
        print(self.image_credits)
        self.image_source_name = args.image_source_name
        self.image_source = args.image_source
        self.image_type = args.image_type

    def do_one(self, member, idx):
        new_image = None
        total = 0
        for image in member.images.image:
            total += 1
            if image.title != self.image_title:
                image.publishStop = NOW
                self.logger.info("Setting offline %s", image.title)
            else:
                new_image = image
                self.logger.info("Found new image %s", new_image.title)

        if not new_image:
            new_image = MU.create_image(self.image_file)
            self.logger.info("Creating new image %s", str(new_image))

        self.logger.info("handled %s images", str(total))

        MU.set_image_fields(new_image, title=self.image_title, source=self.image_source, source_name=self.image_source_name, credits=self.image_credits, image_type=self.image_type)

        member.images.image.append(new_image)
        super().do_one(member, idx)

    def filter_image(self, member, ids):
        return type(member) == programUpdateType


if __name__ == "__main__":
    for_all = ForAllDescendantsReplaceImage()
    for_all.command_line()
    for_all.main()



