#!/usr/bin/env python3
import sys

import json_stream
from npoapi import Media
from npoapi.data.api import *
from npoapi.data.media import ProgramTypeEnum


class IterateExample:
    """
    Example how one could use iterate call via python library.
    """



    def __init__(self):
        self.client = Media().configured_login()


    def show_response(self, response):
        data = json_stream.load(response)
        mediaobjects = data['mediaobjects']
        count = 0
        for lazy_mediaobject in mediaobjects:
            count += 1
            mo = json_stream.to_standard_types(lazy_mediaobject)
            sys.stdout.write(str(count) + ':' + str(mo['mid']) + ":" +  mo['titles'][0]['value'] + "\n")
            sys.stdout.flush()
        response.close()


    def iterate_with_dict(self, **kwargs):
        # Made this work in dec 2023
        response = self.client.iterate_raw(form={
            "searches": {
                "types": ["BROADCAST"]
            }
        }, **kwargs)
        self.show_response(response)

    def iterate_with_json(self, **kwargs):
        response = self.client.iterate_raw(form=
        """
        {
          "searches": {
              "types": "BROADCAST"
          }
       }
        """, **kwargs)
        self.show_response(response)


    def iterate_with_xsdata(self, **kwargs):
        """
        TODO, it should be possible to construct he form via xsdata.
        """
        form = MediaForm()
        form.searches = MediaSearchType()
        form.searches.types = [ProgramTypeEnum.BROADCAST]
        response = self.client.iterate_raw(form=form, **kwargs)






if __name__ == '__main__':
    IterateExample().iterate_with_json(profile="bnnvara", properties="none", limit=None)
    #IterateExample().iterate_with_dict() # new



