#!/usr/bin/env python3
import sys

import json_stream
from npoapi import Media
from npoapi.data import poms
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
            sys.stdout.write(str(count) + ':' + str(mo['mid']) + ":" +  mo['titles'][0]['value'] + ":" + mo['type'] + "\n")
            sys.stdout.flush()
        response.close()

    def iterate_with_dict(self, **kwargs):
        """
        Json could quite easily be constructed via a dict
        """
        # Made this work in dec 2023
        response = self.client.iterate_raw(form={
            "searches": {
                "types": ["BROADCAST"]
            }
        }, **kwargs)
        self.show_response(response)

    def iterate_with_json(self, **kwargs):
        """
        It's possible to use a form, just as json string
        """
        response = self.client.iterate_raw(form=
        """
        {
          "searches": {
              "types": "BROADCAST",
          }
        }
        """, **kwargs)
        self.show_response(response)


    def iterate_with_xsdata(self, **kwargs):
        """
        The form can be more formally constructed via xsdata objects
        """
        form = MediaForm()
        form.searches = MediaSearchType()
        form.searches.types = TextMatcherListType()
        m = TextMatcherType()
        m.value = ProgramTypeEnum.BROADCAST
        form.searches.types.matcher.append(m)
        self.client.logger.info(poms.to_xml(form))
        response = self.client.iterate_raw(form=form, **kwargs)
        self.show_response(response)

if __name__ == '__main__':
    IterateExample().iterate_with_xsdata(profile="bnnvara", properties="none", limit=None)
    #IterateExample().iterate_with_json(profile="bnnvara", properties="none", limit=None)
    #IterateExample().iterate_with_dict(profile="bnnvara", properties="none", limit=None)



