#!/usr/bin/env python3
from npoapi.xml.mediaupdate import programUpdateType
from npoapi.xml.mediaupdate import segmentUpdateType

from for_all_descendants import ForAllDescendants
import datetime
from npoapi import MediaBackendUtil as MU

NOW = datetime.datetime.utcnow()


class ForAllDescendantsReplaceImage(ForAllDescendants):

    def __init__(self, file = None, credits = None, title = None, source_name = None, image_source = None, image_type = 'PICTURE', **kwargs):
        super().__init__(
            processor = self.nope,
            filter = self.filter_image,
            filter_description= "Should be program or segment", **kwargs)
        self.description = "Replacing image"
        self.image_file = file
        self.image_title = title
        self.image_credits = credits
        self.image_source_name = source_name
        self.image_source = image_source
        self.image_type = image_type

    def command_line(self):
        super().command_line()
        self.api.add_argument("image_file", type=str, nargs=1, help='image file name(s)')
        self.api.add_argument("image_title", type=str, nargs=1, help='image title')
        self.api.add_argument("--image_credits", type=str, default=self.image_credits, help='image credits')
        self.api.add_argument("--image_source_name", type=str, default=self.image_source_name, help='image source name')
        self.api.add_argument("--image_source", type=str, default=self.image_source, help='image source')
        self.api.add_argument("--image_license", type=str, default='COPYRIGHTED', help='image license')
        self.api.add_argument("--image_type", type=str, default=self.image_type, help='image type')
        self.api.add_argument("--filter", type=str, default=None, help="""
Filter. A piece of python code to filter. E.g. "memberType == npoapi.xml.mediaupdate.programUpdateType" or "member.type == 'PROMO'"
""")

    def parse_args(self):
        super().parse_args()
        args = self.api.parse_args()
        self.image_file = args.image_file[0]
        self.image_title = args.image_title[0]
        self.image_credits = args.image_credits
        self.image_source_name = args.image_source_name
        self.image_source = args.image_source
        self.image_type = args.image_type
        self.image_license = args.image_license
        f  = args.filter
        if not f is None:
            self.filter = lambda member, idx: eval(f)
            self.filter_description = "specified on command line"


    def process(self, member, idx):
        new_image = None
        needs_post = False
        total_existing = 0
        total_new = 0
        for image in member.images.image:
            if image.title != self.image_title:
                total_existing += 1
                self.logger.debug("%s, %s != %s", str(idx), image.title, self.image_title)
                image.publishStop = NOW
                needs_post = True
            else:
                new_image = image
                self.logger.debug("%s Found existing new image %s", str(idx), new_image.title)


        if not new_image:
            image_files = self.image_file.split(",")
            image_file_to_use = image_files[idx % len(image_files)]
            total_new += 1
            new_image = MU.create_image(image_file_to_use)
            needs_post = True
            MU.set_image_fields(
                new_image,
                title=self.image_title, source=self.image_source,
                source_name=self.image_source_name,
                credits=self.image_credits,
                license=self.image_license,
                image_type=self.image_type)
            self.logger.info("%s Creating new image %s %s", str(idx), str(new_image.title), image_file_to_use)
            member.images.image.append(new_image)

        self.logger.info("%s handled %s existing images, and created %s", str(idx), str(total_existing), str(total_new))

        return needs_post


    @staticmethod
    def filter_image(member, ids):
        return type(member) == programUpdateType or type(member) == segmentUpdateType


if __name__ == "__main__":
    ForAllDescendantsReplaceImage().main()



