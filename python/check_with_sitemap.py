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

import datetime
import io
import json
import os
import pickle
import re
import urllib
import xml.etree.ElementTree

import pyxb
import requests
from npoapi import Pages
from npoapi import PagesBackend
from npoapi.xml import poms

api = Pages().command_line_client()
backend = PagesBackend(env=api.actualenv).configured_login()
api.add_argument('sitemap', type=str, nargs=1, help='sitemap')
api.add_argument('profile', type=str, nargs='?', help='profile')
api.add_argument('-C', '--clean', action='store_true', default=False, help='clean build')
api.add_argument('-D', '--delete', action='store_true', default=False, help='delete from api')
api.add_argument('-A', '--add', action='store_true', default=False, help='add to api')
api.add_argument('-S', '--show', action='store_true', default=False, help='show from api')
api.add_argument('--use_database', action='store_true', default=False, help='clean build')
api.add_argument('--https_to_http', action='store_true', default=False, help='Replace all https with http')
api.add_argument('--http_to_https', action='store_true', default=False, help='Replace all http with https')
api.add_argument('--post_process_sitemap', type=str, default=None, help='')
api.add_argument('--post_process_api', type=str, default=None, help='')
api.add_argument('--post_process', type=str, default=None, help='')
api.add_argument('--target_directory', type=str, default=None, help='')

args = api.parse_args()

profile = args.profile
sitemap_url = args.sitemap[0]
clean = args.clean
delete_from_api = args.delete
add_docs_to_api = args.add
show_docs_from_api = args.show
https_to_http = args.https_to_http
http_to_https = args.http_to_https
use_database = args.use_database
log = api.logger

if use_database and clean:
    raise Exception("Can't use both use_database and clean")

if https_to_http and http_to_https:
    raise Exception("Can't set both https_to_http and http_to_https")
if args.target_directory:
    target_directory = args.target_directory
    log.info("Target directory: %s" % target_directory)
    if not os.path.exists(target_directory):
        log.info("Created")
        os.makedirs(target_directory)
else:
    target_directory = ""



if clean:
    log.info("Cleaning")

log.info("API: %s, profile: %s" % (api.url, profile))


def file_in_target(file: str) -> str:
    return os.path.join(target_directory, file)

def get_urls_from_api_search() -> set:
    offset = 0
    new_urls = set()
    while True:
        result = api.search(profile=profile, offset=offset, limit=240)
        json_object = json.loads(result)
        items = json_object['items']
        total = json_object['total']
        log.info("API: Found %s/%s urls for profile %s", len(new_urls), total, profile)
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
    today = now.replace(hour=6, minute=0, second=0, microsecond=0)
    dateRange = API.dateRangeMatcherType(end=today)
    form.searches.creationDates.append(dateRange)
    pages = api.iterate(profile=profile, form=form)
    for page in pages:
        new_urls.add(page['url'])
        if len(new_urls) % 100 == 0:
            log.info("API: Found %s urls for profile %s", len(new_urls), profile)

    return new_urls


def get_urls() -> list:
    url_file = file_in_target("data." + profile + ".p")
    if use_database or (os.path.exists(url_file) and not clean):
        new_urls = pickle.load(open(url_file, "rb"))
    else:
        # new_urls = get_urls_from_api_search()
        new_urls = get_urls_from_api_iterate()
        pickle.dump(new_urls, open(url_file, "wb"))

    dest_file = file_in_target("data." + profile + ".txt")
    with io.open(dest_file, 'w', encoding="utf-8") as f:
        f.write('\n'.join(sorted(new_urls)))
    log.info("Wrote %s (%d entries)", dest_file, len(new_urls))
    return list(new_urls)


def get_sitemap_from_xml() -> list:
    log.debug("Opening %s", sitemap_url)
    response = urllib.request.urlopen(sitemap_url)
    locs = set()
    for ev, el in xml.etree.ElementTree.iterparse(response):
        if el.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}loc":
            locs.add(el.text)
    response.close()
    new_urls = set()
    for loc in locs:
        #print(loc)
        response = urllib.request.urlopen(loc)
        for ev, el in xml.etree.ElementTree.iterparse(response):
            if el.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}loc":
                url = el.text
                new_urls.add(url)
                if len(new_urls) % 1000 == 0:
                    log.info("Sitemap: %s urls", len(new_urls))
        response.close()

    return list(new_urls)


def get_sitemap() -> list:
    sitemap_file = file_in_target("data." + profile + ".sitemap.p")
    if use_database or (os.path.exists(sitemap_file) and not clean):
        new_urls = pickle.load(open(sitemap_file, "rb"))
    else:
        new_urls = get_sitemap_from_xml()
        pickle.dump(new_urls, open(sitemap_file, "wb"))

    dest_file = file_in_target("data." + profile + ".sitemap.txt")
    with io.open(dest_file, 'w', encoding="utf-8") as f:
        f.write('\n'.join(sorted(new_urls)))
    log.info("Wrote %s (%d entries)", dest_file, len(new_urls))

    return new_urls


def http_status(url):
    try:
        resp = requests.head(url, allow_redirects=False)
        return resp.status_code
    except Exception as e:
        api.logg.info("%e", str(e))
        return 404


def unmap(mapped_urls: list, urls: list, url: str):
    try:
        i = mapped_urls.index(url)
        return urls[i]
    except ValueError:
        log.error("Could not map")
        return ""

def clean_from_api(
        mapped_api_urls: list,
        api_urls: list,
        mapped_sitemap_urls: list):
    """Explores what needs to be cleaned from the API, and (optionally) also tries to do that."""
    dest_file = file_in_target("report." + profile + "in_api_but_not_in_sitemap.txt")

    if not os.path.exists(dest_file) or clean:
        log.info("Calculating what needs to be removed from api")
        mapped_not_in_sitemap = set(mapped_api_urls) - set(mapped_sitemap_urls)
        # translate to actual urls
        not_in_sitemap = sorted(list(set(map(lambda url: unmap(mapped_api_urls, api_urls, url), mapped_not_in_sitemap))))

        with io.open(dest_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(list(not_in_sitemap))))
            log.info("Wrote to %s" % dest_file)
    else:
        with io.open(dest_file, 'r', encoding='utf-8') as f:
            not_in_sitemap = f.read().splitlines()
            log.info("Read from %s" % f.name)

    log.info("In api but not in sitemap: %s" % len(not_in_sitemap))

    if delete_from_api:
        clean_from_es = file_in_target("todo." + profile + "_should_be_removed_from_es.txt")
        remove_from_api = file_in_target("done." + profile + "_removed_from_api.txt")
        log.info("Deleting from api")
        with io.open(clean_from_es, 'w', encoding='utf-8') as f_clean_from_es:
            with io.open(remove_from_api, 'w', encoding='utf-8') as f_remove_from_api:

                for idx, url in enumerate(not_in_sitemap):
                    status = http_status(url)
                    if status == 404 or status == 301:
                        log.info("(%d/%d) Deleting %s", idx, len(not_in_sitemap), url)
                        response = backend.delete(url)
                        log.info("%s" % response)
                        if response == "NOTFOUND":
                            f_clean_from_es.write(url + '\n')
                        else :
                            f_remove_from_api.write(url + '\n')
                    else:
                        result = backend.get(url)
                        if not result is None:
                            page = poms.CreateFromDocument(result)
                            log.info("(%d/%d) In api, not in sitemap, but not giving 404 (but %s) url %s: %s", idx, len(not_in_sitemap), str(status), url, str(page.lastPublished))
                        else:
                            log.info("(%d/%d) In api, not giving 404 (but %s), but not found in publisher %s", idx, len(not_in_sitemap), str(status), url)
    else:
        log.info("No actual deletes requested")



def add_to_api(
        mapped_api_urls: list,
        mapped_sitemap_urls: list,
        sitemap_urls:list):
    """Explores what needs to be added to the API"""
    dest_file = file_in_target("report." + profile + "_in_sitemap_but_not_in_api.txt")
    not_in_api = ()
    if  not os.path.exists(dest_file) or clean:
        log.info("Calculating what needs to be added to the api")
        mapped_not_in_api = set(mapped_sitemap_urls) - set(mapped_api_urls)
        not_in_api = sorted(list(set(map(lambda url: unmap(mapped_sitemap_urls, sitemap_urls, url), mapped_not_in_api))))

        with io.open(dest_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(not_in_api))
            print("Wrote to %s" % f.name)

    else:
        with io.open(dest_file, 'r', encoding='utf-8') as f:
            not_in_api = f.read().splitlines()
            log.info("Read from %s" % f.name)

    log.info("In sitemap but not in api: %s" % len(not_in_api))

    for url in not_in_api[:10]:
        print(url)




def main():

    # list of all urls as they are present in the page api
    api_urls = get_urls()
    # list of all urls as there are present in the sitemap
    sitemap_urls = get_sitemap()

    post_process = lambda url: url
    if args.post_process:
        post_process = eval(args.post_process)

    post_process_sitemap = lambda url: url
    post_process_api = lambda url: url

    if args.post_process_sitemap:
        post_process_sitemap = eval(args.post_process_sitemap)

    if args.post_process_api:
        post_process_api = eval(args.post_process_api)

    schema_mapper = lambda url: url
    if https_to_http:
        schema_mapper = lambda url: re.sub(r'^https://(.*)', r'http://\1', url)

    if http_to_https:
        schema_mapper = lambda url: re.sub(r'^http://(.*)', r'https://\1', url)

    log.info("Post processing")
    # list of all urls as they are present in the page api, but post processed. Should be used for comparing, not for operations
    mapped_api_urls = list(map(lambda url: post_process(post_process_api(schema_mapper(url))), api_urls))
    # list of all urls as they are present in the sitemap, but post processed. Should be used for comparing, not for operations
    mapped_sitemap_urls = list(map(lambda url: post_process(post_process_sitemap(schema_mapper(url))), sitemap_urls))
    log.info(".")

    clean_from_api(
        mapped_api_urls,
        api_urls,
        mapped_sitemap_urls)

    add_to_api(
        mapped_api_urls,
        mapped_sitemap_urls,
        sitemap_urls)


if __name__ == "__main__":
    main()
    print("Ready.")
