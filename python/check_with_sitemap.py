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
import pyxb
import datetime



api = Pages().command_line_client()
backend = PagesBackend(env=api.actualenv).configured_login()
api.add_argument('sitemap', type=str, nargs=1, help='sitemap')
api.add_argument('profile', type=str, nargs='?', help='profile')
api.add_argument('-C', '--clean', action='store_true', default=False, help='clean build')
api.add_argument('-D', '--delete', action='store_true', default=False, help='delete from api')
api.add_argument('--https_to_http', action='store_true', default=False, help='Replace all https with http')
api.add_argument('--http_to_https', action='store_true', default=False, help='Replace all http with https')
api.add_argument('--post_process_sitemap', type=str, default=None, help='')
api.add_argument('--post_process_api', type=str, default=None, help='')
api.add_argument('--post_process', type=str, default=None, help='')

args = api.parse_args()

profile = args.profile
sitemap_url = args.sitemap[0]
clean = args.clean
delete_from_api = args.delete
https_to_http = args.https_to_http
http_to_https = args.http_to_https
if https_to_http and http_to_https:
    raise Exception("Can't set both https_to_http and http_to_https")

if clean:
    api.logger.info("Cleaning")


def get_urls_from_api_search() -> set:
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
            new_urls.add(url)
            offset += 1
            grow += 1

        if grow == 0:
            break
    return new_urls


def get_urls_from_api_iterate() -> set:
    new_urls = set()
    from npoapi.xml import api as API
    form = API.pagesForm()
    form.sortFields = pyxb.BIND()
    form.sortFields.append(API.pageSortTypeEnum.creationDate)
    form.searches = pyxb.BIND()
    form.searches.creationDates = pyxb.BIND()
    now = datetime.datetime.now()
    today = now.replace(hour = 6, minute=0, second=0, microsecond=0)
    dateRange = API.dateRangeMatcherType(end=today)
    form.searches.creationDates.append(dateRange)
    pages = api.iterate(profile=profile, form=form)
    for page in pages:
        new_urls.add(page['url'])
        if len(new_urls) % 100 == 0:
            api.logger.info("API: Found %s urls for profile %s", len(new_urls), profile)

    return new_urls


def get_urls() -> list:
    url_file = "/tmp/" + profile + ".p"
    if os.path.exists(url_file) and not clean:
        new_urls = pickle.load(open(url_file, "rb"))
    else:
        #new_urls = get_urls_from_api_search()
        new_urls = get_urls_from_api_iterate()
        pickle.dump(new_urls, open(url_file, "wb"))

    with codecs.open(profile + ".txt", 'w', "utf-8") as f:
        f.write('\n'.join(sorted(new_urls)))
    api.logger.info("Wrote %s", profile + ".txt")

    return list(new_urls)


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


def clean_from_api(mapped_api_urls: list,
                   api_urls: list,
                   mapped_sitemap_urls: list,
                   sitemap_urls: list
                   ):

    mapped_not_in_sitemap = set(mapped_api_urls) - set(mapped_sitemap_urls)
    not_in_sitemap = set(map(lambda url: api_urls[mapped_api_urls.index(url)], mapped_not_in_sitemap))
    print("in api but not in sitemap: %s" % len(not_in_sitemap))
    with codecs.open('in_' + profile + '_but_not_in_sitemap.txt', 'w', 'utf-8') as f:
        f.write('\n'.join(sorted(list(not_in_sitemap))))
    if delete_from_api:
        for idx, url in enumerate(not_in_sitemap):
            status = http_status(url)
            if status == 404 or status == 301:
                api.logger.info("Deleting %s", url)
                backend.delete(url)
            else:
                result = backend.get(url)
                if not result is None:
                    page = poms.CreateFromDocument(result)
                    api.logger.info("In api, not in sitemap, but not giving 404 (but %s) url %s: %s", str(status), url, str(page.lastPublished))
                else:
                    api.logger.info("In api, not giving 404 (but %s), but not found in publisher %s", str(status), url)
                # print(url, http_status(url))


def add_to_api(
        mapped_api_urls: list,
        api_urls:list,
        mapped_sitemap_urls: list,
        sitemap_urls:list):
    mapped_not_in_api = set(mapped_sitemap_urls) - set(mapped_api_urls)
    not_in_api = set(map(lambda url: api_urls[mapped_api_urls.index(url)], mapped_not_in_api))
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
    api_urls = get_urls()
    sitemap_urls = get_sitemap()

    post_process = lambda url: url
    if args.post_process:
        post_process = eval(args.post_process)

    post_process_sitemap = lambda url: url
    post_process_api = lambda url: url


    if args.post_process_sitemap:
        post_process_sitemap = eval(args.post_process_sitemap)

    if args.post_process_api:
        post_process_api= eval(args.post_process_api)

    schema_mapper = lambda url: url
    if https_to_http:
        schema_mapper  = lambda url: re.sub(r'^https://(.*)', r'http://\1', url)

    if http_to_https:
        schema_mapper = lambda url: re.sub(r'^http://(.*)', r'https://\1', url)


    mapped_api_urls = list(map(lambda url: post_process(post_process_api(schema_mapper(url))), api_urls))
    mapped_sitemap_urls = list(map(lambda url: post_process(post_process_sitemap(schema_mapper(url))), sitemap_urls))

    clean_from_api(mapped_api_urls,
                   api_urls,
                   mapped_sitemap_urls, sitemap_urls)
    add_to_api(api_urls,
               sitemap_urls
               )


if __name__ == "__main__":
    main()




