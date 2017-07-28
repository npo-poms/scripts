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

from npoapi import Pages
from npoapi import PagesBackend
from npoapi.xml import poms
import json
import pickle
import os
import urllib
import xml.etree.ElementTree
import re
import codecs

api = Pages().command_line_client()
backend = PagesBackend(env=api.actualenv).configured_login()
api.add_argument('sitemap', type=str, nargs=1, help='sitemap')
api.add_argument('profile', type=str, nargs='?', help='profile')
api.add_argument('-C', '--clean', action='store_true', default=False, help='clean build')
api.add_argument('-D', '--delete', action='store_true', default=False, help='delete from api')
api.add_argument('--https_to_http', action='store_true', default=False, help='Replace all https with http')

args = api.parse_args()

profile = args.profile
sitemap_url = args.sitemap[0]
clean = args.clean
delete_from_api = args.delete
https_to_http = args.https_to_http

if clean:
    api.logger.info("Cleaning")


def get_urls_from_api() -> set:
    offset = 0
    new_urls = set()
    while True:
        result = api.search(profile=profile, offset=offset, limit=240)
        json_object = json.loads(result)
        items = json_object['items']
        total = json_object['total']
        api.logger.info("API: Found %s/%s urls for profile %s", len(new_urls), total, profile)
        grow = 0
        for item in items:
            url = item['result']['url']
            if https_to_http:
                url = re.sub(r'^https://(.*)', r'http://\1', url)
            new_urls.add(url)
            offset += 1
            grow += 1

        if grow == 0:
            break
    return new_urls


def get_urls() -> set:
    url_file = "/tmp/urls." + profile + ".p"
    if os.path.exists(url_file) and not clean:
        new_urls = pickle.load(open(url_file, "rb"))
    else:
        new_urls = get_urls_from_api()
        pickle.dump(new_urls, open(url_file, "wb"))

    with codecs.open(profile + ".txt", 'w', "utf-8") as f:
        f.write('\n'.join(sorted(new_urls)))
    api.logger.info("Wrote %s", profile + ".txt")

    return set(new_urls)


def get_sitemap_from_xml():
    api.logger.debug("Opening %s", sitemap_url)
    response = urllib.request.urlopen(sitemap_url)
    locs = set()
    for ev, el in xml.etree.ElementTree.iterparse(response):
        if el.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}loc":
            locs.add(el.text)
    response.close()
    new_urls = set()
    for loc in locs:
        print(loc)
        response = urllib.request.urlopen(loc)
        for ev, el in xml.etree.ElementTree.iterparse(response):
            if el.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}loc":
                url = el.text
                new_urls.add(url)
                if len(new_urls) % 1000 == 0:
                    api.logger.info("Sitemap: %s urls", len(new_urls))
        response.close()


    return new_urls


def get_sitemap():
    sitemap_file = "/tmp/" + profile + ".sitemap.p"
    if os.path.exists(sitemap_file) and not clean:
        new_urls = pickle.load(open(sitemap_file, "rb"))
    else:
        new_urls = get_sitemap_from_xml()
        pickle.dump(new_urls, open(sitemap_file, "wb"))

    with codecs.open(profile + ".sitemap.txt", 'w', "utf-8") as f:
        f.write('\n'.join(sorted(new_urls)))
    api.logger.info("Wrote %s", profile + ".sitemap.txt")

    return new_urls

def http_status(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req)
        return resp.status
    except Exception as ue:
        return ue.status


def clean_from_api(urls:set, sitemap:set):
    not_in_sitemap = urls - sitemap
    print("in api but not in sitemap: %s" % len(not_in_sitemap))
    with codecs.open('in_' + profile + '_but_not_in_sitemap.txt', 'w', 'utf-8') as f:
        f.write('\n'.join(sorted(list(not_in_sitemap))))
    if delete_from_api:
        for idx, url in enumerate(not_in_sitemap):
            status = http_status(url)
            if status == 404:
                api.logger.info("Deleting %s", url)
                backend.delete(url)
            else:
                page = poms.CreateFromDocument(backend.get(url))
                api.logger.info("In api, not in sitemap, but not giving 404 url %s: %s", url, str(page.lastPublished))
                # print(url, http_status(url))


def add_to_api(urls:set, sitemap:set):
    not_in_api = sitemap - urls
    print("in sitemap but not in api: %s" % len(not_in_api))
    with codecs.open('in_sitemap_but_not_in_' + profile + ".txt", 'w', 'utf-8') as f:
        f.write('\n'.join(sorted(list(not_in_api))))

    print("Wrote to %s" % f.name)
    for url in list(not_in_api)[:10]:
        print(url)
        from_backend = backend.get(url)
        from_frontend = api.get(url)
        if from_backend:
            page = poms.CreateFromDocument(from_backend)


def main():
    got_urls = get_urls()
    got_sitemap = get_sitemap()

    if https_to_http:
        mapped_urls = set(map(lambda url: re.sub(r'^https://(.*)', r'http://\1', url), got_urls))
        with codecs.open(profile + ".mapped.txt", 'w', "utf-8") as f:
            f.write('\n'.join(sorted(mapped_urls)))
        mapped_sitemap = set(map(lambda url: re.sub(r'^https://(.*)', r'http://\1', url), got_sitemap))
        with codecs.open(profile + ".sitemap.mapped.txt", 'w', "utf-8") as f:
            f.write('\n'.join(sorted(mapped_sitemap)))
    else:
        mapped_urls = got_urls
        mapped_sitemap = got_sitemap


    clean_from_api(mapped_urls, mapped_sitemap)
    add_to_api(mapped_urls, mapped_sitemap)


if __name__ == "__main__":
    main()




