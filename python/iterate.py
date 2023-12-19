#!/usr/bin/env python3
import sys

import json_stream
from npoapi import Media
from npoapi.data.api import MediaForm


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
            sys.stdout.write(str(count) + ':' + str(mo['mid']) + mo['titles'][0]['value'] + "\n")
            sys.stdout.flush()
        response.close()


    def iterate_with_dict(self):
        # Made this work in dec 2023
        response = self.client.iterate_raw(form={
            "searches": {
                "types": ["BROADCAST"]
            }
        }, profile="vpro", limit=None, properties="all")
        self.show_response(response)

    def iterate_with_json(self):
        response = self.client.iterate_raw(form=
        """
        {
          "searches": {
              "types": "BROADCAST"
          }
       }
        """, profile="vpro")
        self.show_response(response)



    def iterate_with_xsdata(self):
        """
        TODO, it should be possible to constructt he form via xsdata.
        """
        form = MediaForm()







if __name__ == '__main__':
    IterateExample().iterate_with_json()
    #IterateExample().iterate_with_dict() # new



