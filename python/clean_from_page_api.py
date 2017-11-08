#!/usr/bin/env python3
"""
This script has two arguments. A sitemap url and a api profile.

It will download the entire profile from the NPO Front end api, and it will also download the entire sitemap.

Then, it compares the found URL's in both. They should represent the same set.

If there are URL in the API which are not in the Sitemap, which are indeed not existing (give 404's) then the script
supposes this is an error and deletes the object from the API.

If objects are in the API but not in the sitemap, then we suppose the sitemap is outdated.

If objects are in the sitemap but not in the API then there are two possibilities
  - The object is in the API, but not in the profile
  - The object does not existing in the API at all

In both cases the object needs the be reindexed from the CMS.
"""

import json

import os

import pickle
import requests
from npoapi import Pages
from npoapi import PagesBackend
import urllib.parse

api = Pages().command_line_client()
backend = PagesBackend(env=api.actualenv).configured_login()
api.add_argument('profile', type=str, nargs='?', help='profile')
args = api.parse_args()

profile = args.profile


def filter(item):
    return True

def get_urls_from_api_search(max=None) -> set:
    offset = 0
    new_urls = set()
    total = None
    while True:
        if total != None:
            api.logger.info("API: Found %s/%s/%s urls for profile %s", len(new_urls), offset, total, profile)
        result = api.search(profile=profile, offset=offset, limit=240, form="{}")
        json_object = json.loads(result)
        items = json_object['items']
        total = json_object['total']
        grow = 0
        for item in items:
            url = item['result']['url']
            if url.startswith("http:"):
                print(url)
                new_urls.add(url)
            for crid in item['result']['crids']:
                if crid.startswith("crid://vpro/media/vpro/"):
                    new_urls.add(url)
            offset += 1
            grow += 1

        if grow == 0 or (max != None and len(new_urls) > max):
            break
    return new_urls

def main():
    url_file = "/tmp/" + profile + ".p"
    if os.path.exists(url_file):
        api_urls= pickle.load(open(url_file, "rb"))
    else:
        api_urls = get_urls_from_api_search()
        pickle.dump(api_urls, open(url_file, "wb"))

    for api_url in api_urls:
        backend.delete(api_url)
        api_url_encoded = urllib.request.quote(api_url, safe='')
        print(api_url + "-> " + api_url_encoded)
        es_url = 'http://localhost:9208/apipages/page/' + api_url_encoded
        print(es_url)
        requests.delete(es_url)
    print(api_urls)



if __name__ == "__main__":
    main()




