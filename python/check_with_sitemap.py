#!/usr/bin/env python3
"""
"""

from npoapi import Pages
import json
import pickle
import os
import urllib
import xml.etree.ElementTree

api = Pages().command_line_client()
api.add_argument('sitemap', type=str, nargs=1, help='sitemap')
api.add_argument('profile', type=str, nargs='?', help='profile')
api.add_argument('-C', '--clean', action='store_true', default=False, help='clean')

args = api.parse_args()

profile = args.profile
sitemap = args.sitemap[0]
clean = args.clean

if clean:
    print("Cleaning")

def get_urls_from_api() -> set:
    offset = 0
    urls = set()
    while True:
        result = api.search(profile=args.profile, offset=offset, limit=240)
        json_object = json.loads(result)
        items = json_object['items']
        total = json_object['total']
        api.logger.info("API: Found %s/%s urls", len(urls), total)
        grow = 0
        for item in items:
            url = item['result']['url']
            urls.add(url)
            offset += 1
            grow += 1

        if grow == 0:
            break
    return urls


def get_urls() -> set:
    url_file = "/tmp/urls." + profile + ".p"
    if os.path.exists(url_file) and not clean:
        urls = pickle.load(open(url_file, "rb"))
    else:
        urls = get_urls_from_api()
        pickle.dump(urls, open(url_file, "wb"))
    return urls


def get_sitemap_from_xml():
    response = urllib.request.urlopen(sitemap)
    locs = set()
    for ev, el in xml.etree.ElementTree.iterparse(response):
        if el.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}loc":
            locs.add(el.text)
    response.close()
    urls = set()
    for loc in locs:
        print(loc)
        response = urllib.request.urlopen(loc)
        for ev, el in xml.etree.ElementTree.iterparse(response):
            if el.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}loc":
                urls.add(el.text)
                if len(urls) % 1000 == 0:
                    api.logger.info("Sitemap: %s urls", len(urls))
        response.close()
    return urls


def get_sitemap():
    sitemap_file = "/tmp/" + profile + ".sitemap.p"
    if os.path.exists(sitemap_file) and not clean:
        urls = pickle.load(open(sitemap_file, "rb"))
    else:
        urls = get_sitemap_from_xml()
        pickle.dump(urls, open(sitemap_file, "wb"))
    return urls

urls = get_urls()
sitemap = get_sitemap()

print("in api but not in sitemap: %s" % len(urls - sitemap))
for url in list(urls - sitemap)[:10]:
    print(url)
print("in sitemap but not in api: %s" % len(sitemap - urls))
for url in list(sitemap - urls)[:10]:
    print(url)

