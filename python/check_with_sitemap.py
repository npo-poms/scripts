#!/usr/bin/env python3
"""
This script has two arguments. A sitemap url and a api profile.

It will download the entire profile from the NPO Front end api, and it will also download the entire sitemap.

Then, it compares the found URL's in both. They should represent the same set.

If there are URL in the API which are not in the Sitemap, which are indeed not existing (give 404's) then the script
supposes this is an error and can delete the object from the API (if --delete is specified)

If objects are in the API but not in the sitemap, then we suppose the sitemap is outdated.

If objects are in the sitemap but not in the API then there are two possibilities
  - The object is in the API, but not in the profile
  - The object does not existing in the API at all

In both cases the object needs the be reindexed from the CMS.
"""

import datetime
import io
import os
import pickle
import re
import urllib
import xml.etree.ElementTree

import pyxb
import requests
from npoapi import Pages
from npoapi import PagesBackend


class CheckWithSitemap:
    def __init__(self):
        self.api = Pages().command_line_client()
        self.backend = PagesBackend(env=self.api.actualenv).configured_login()
        self.add_arguments()
        self.args = self.api.parse_args()

        args = self.args
        self.profile = args.profile
        self.sitemap_url = args.sitemap[0]
        self.clean = args.clean
        self.get_check = not args.no_get_check
        self.delete_from_api = args.delete
        self.show_docs_from_api = args.show
        self.https_to_http = args.https_to_http
        self.http_to_https = args.http_to_https
        self.use_database = args.use_database

        self.log = self.api.logger

        if self.use_database and self.clean:
            raise Exception("Can't use both use_database and clean")

        if self.https_to_http and self.http_to_https:
            raise Exception("Can't set both https_to_http and http_to_https")
        if args.target_directory:
            self.target_directory = args.target_directory
            self.log.info("Target directory: %s" % self.target_directory)
            if not os.path.exists(self.target_directory):
                self.log.info("Created")
                os.makedirs(self.target_directory)
        else:
            self.target_directory = ""

        if self.clean:
            self.log.info("Cleaning")

        self.log.info("API: %s, profile: %s" % (self.api.url, self.profile))

    def add_arguments(self):
        api = self.api
        api.add_argument('sitemap', type=str, nargs=1, help='URL to the sitemap')
        api.add_argument('profile', type=str, nargs='?', help='NPO pages profile')
        api.add_argument('-C', '--clean', action='store_true', default=False, help='clean build')
        api.add_argument('-D', '--delete', action='store_true', default=False, help='remove from api')
        api.add_argument('--no_get_check', action='store_true', default=False, help='when removing from api, dont check http status code first (only 404s will be deleted)')
        api.add_argument('-S', '--show', action='store_true', default=False, help='show from api')
        api.add_argument('--use_database', action='store_true', default=False, help='explicitly use the local database (inverse of clean)')
        api.add_argument('--https_to_http', action='store_true', default=False, help='Replace all https with http')
        api.add_argument('--http_to_https', action='store_true', default=False, help='Replace all http with https')
        api.add_argument('--post_process_sitemap', type=str, default=None, help='')
        api.add_argument('--post_process_api', type=str, default=None, help='')
        api.add_argument('--post_process', type=str, default=None, help='')
        api.add_argument('--target_directory', type=str, default=None, help='')



    def file_in_target(self, file: str) -> str:
        return os.path.join(self.target_directory, file)

    def get_urls_from_api_iterate(self, until = None) -> set:
        """
        Gets all urls as they are in the pages api

        :param datetime.datetime until:a constraint on creationdate. Defaults to 6 o'clock today
        """
        new_urls = set()
        from npoapi.xml import api as API
        form = API.pagesForm()
        form.sortFields = pyxb.BIND()
        form.sortFields.append(API.pageSortTypeEnum.creationDate)
        form.searches = pyxb.BIND()
        form.searches.creationDates = pyxb.BIND()
        if not until:
            now = datetime.datetime.now()
            until = now.replace(hour=6, minute=0, second=0, microsecond=0)

        pages = self.api.iterate(profile=self.profile, form=form)
        for page in pages:
            if 'creationDate' in page:
                creationDate = datetime.datetime.fromtimestamp(page['creationDate'] / 1000)
            else:
                creationDate = datetime.datetime.fromtimestamp(0)
            url = page['url']
            if creationDate < until:
                new_urls.add(url)
            else:
                self.log.info("Ignoring %s since it is newer (%s) than sitemap itself" % (url, str(creationDate)))
            if len(new_urls) % 100 == 0:
                self.log.info("API: Found %d urls for profile %s" % (len(new_urls), self.profile))

        return new_urls

    def get_urls(self) -> list:
        url_file = self.file_in_target("data." + self.profile + ".api.p")
        if self.use_database or (os.path.exists(url_file) and not self.clean):
            new_urls = pickle.load(open(url_file, "rb"))
        else:
            if os.path.exists(url_file):
                if self.clean:
                    self.log.info("Ignoring %s because of clean parameter" % url_file)
            else:
                self.log.info("No %s found, creating it now" % url_file)
            # new_urls = get_urls_from_api_search()
            new_urls = sorted(self.get_urls_from_api_iterate())
            #new_urls = sorted(get_urls_from_api_iterate(datetime.datetime.now()))
            pickle.dump(new_urls, open(url_file, "wb"))

        self.write_urls_to_file(new_urls, "data." + self.profile + ".api.txt")

        return list(new_urls)

    def get_sitemap_from_xml(self) -> list:
        self.log.debug("Opening %s", self.sitemap_url)
        response = urllib.request.urlopen(self.sitemap_url)
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
                        self.log.info("Sitemap: %s urls", len(new_urls))
            response.close()

        return list(new_urls)

    def write_urls_to_file(self, urls: list, file_name : str):
        dest_file = self.file_in_target(file_name)
        with io.open(dest_file, 'w', encoding="utf-8") as f:
            f.write('\n'.join(urls))
            f.write('\n')
        self.log.info("Wrote %s (%d entries)", dest_file, len(urls))

    def get_sitemap(self) -> list:
        sitemap_file = self.file_in_target("data." + self.profile + ".sitemap.p")
        if self.use_database or (os.path.exists(sitemap_file) and not self.clean):
            new_urls = pickle.load(open(sitemap_file, "rb"))
        else:
            new_urls = sorted(self.get_sitemap_from_xml())
            pickle.dump(new_urls, open(sitemap_file, "wb"))

        self.write_urls_to_file(new_urls, "data." + self.profile + ".sitemap.txt")

        return new_urls

    def http_status(self, url):
        try:
            resp = requests.head(url, allow_redirects=False)
            return resp.status_code
        except Exception as e:
            self.log.info("%s" % str(e))
            return 404


    def unmap(self, mapped_urls: list, urls: list, url: str):
        try:
            i = mapped_urls.index(url)
            return urls[i]
        except ValueError:
            self.log.error("Could not map")
            return ""


    def clean_from_api(self,
            mapped_api_urls: list,
            api_urls: list,
            mapped_sitemap_urls: list):
        """Explores what needs to be cleaned from the API, and (optionally) also tries to do that."""
        dest_file_name = "report." + self.profile + ".in_api_but_not_in_sitemap.txt"
        dest_file = self.file_in_target(dest_file_name)

        if not os.path.exists(dest_file) or self.clean:
            self.log.info("Calculating what needs to be removed from api")
            mapped_not_in_sitemap = set(mapped_api_urls) - set(mapped_sitemap_urls)
            # translate to actual urls
            not_in_sitemap = sorted(list(set(map(lambda url: self.unmap(mapped_api_urls, api_urls, url), mapped_not_in_sitemap))))

            self.write_urls_to_file(sorted(list(not_in_sitemap)), dest_file_name)
        else:
            with io.open(dest_file, 'r', encoding='utf-8') as f:
                not_in_sitemap = f.read().splitlines()
                self.log.info("Read from %s" % f.name)

        self.log.info("In api but not in sitemap: %s" % len(not_in_sitemap))

        if self.delete_from_api:
            clean_from_es = self.file_in_target("todo." + self.profile + ".should_be_removed_from_es.txt")
            remove_from_api = self.file_in_target("done." + self.profile + ".removed_from_api.txt")
            self.log.info("Deleting from api")
            todo_delete_from_es = 0
            with io.open(clean_from_es, 'w', encoding='utf-8') as f_clean_from_es, \
                    io.open(remove_from_api, 'w', encoding='utf-8') as f_removed_from_api:
                for idx, url in enumerate(not_in_sitemap):
                    if self.get_check:
                        status = self.http_status(url)
                    else:
                        status = None
                    if status is None or status == 404 or status == 301:
                        self.log.info("(%d/%d) Deleting %s (http status: %s)", idx, len(not_in_sitemap), url, str(status))
                        response = self.backend.delete(url)
                        if self.backend.code == 404:
                            self.log.info("Backend gave 404 for delete call: %s", url)
                            f_clean_from_es.write(url + '\n')
                            todo_delete_from_es += 1
                        elif self.backend.code == 400:
                            self.log.info("Backend gave 400 for delete call: %s", url)
                        else:
                            self.log.info("%s" % response)
                            f_removed_from_api.write(url + '\n')
                    else:
                        result = self.backend.get(url)
                        if not result is None:
                            page = self.backend.to_object(result)
                            self.log.info("(%d/%d) In api, not in sitemap, but not giving 404 (but %s) url %s: %s", idx, len(not_in_sitemap), str(status), url, str(page.lastPublished))
                        else:
                            self.log.info("(%d/%d) In api, not giving 404 (but %s), but not found in publisher %s", idx, len(not_in_sitemap), str(status), url)
            if todo_delete_from_es > 0:
                self.log.info("""
    Some things could not be removed from api (gave 404). Wrote to %s. You may want to run
    clean_from_es.sh %s
    """ % (clean_from_es, clean_from_es))

        else:
            self.log.info("No actual deletes requested")


    def perform_add_to_api(self, not_in_api: list):
        """Actually add to api"""
        self.log.info("Not implemented")


    def add_to_api(
            self,
            mapped_api_urls: list,
            mapped_sitemap_urls: list,
            sitemap_urls:list):
        """Explores what needs to be added to the API"""
        dest_file = self.file_in_target("report." + self.profile + ".in_sitemap_but_not_in_api.txt")
        not_in_api = ()
        if  not os.path.exists(dest_file) or self.clean:
            self.log.info("Calculating what needs to be added to the api")
            mapped_not_in_api = set(mapped_sitemap_urls) - set(mapped_api_urls)
            not_in_api = sorted(list(set(map(lambda url: self.unmap(mapped_sitemap_urls, sitemap_urls, url), mapped_not_in_api))))

            with io.open(dest_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(not_in_api))
                print("Wrote to %s" % f.name)

        else:
            with io.open(dest_file, 'r', encoding='utf-8') as f:
                not_in_api = f.read().splitlines()
                self.log.info("Read from %s" % f.name)

        self.log.info("In sitemap but not in api: %s urls. E.g.:" % len(not_in_api))

        for url in not_in_api[:10]:
            print(url)

        self.perform_add_to_api(not_in_api)

    def main(self):
        # list of all urls as they are present in the page api
        api_urls = self.get_urls()
        # list of all urls as there are present in the sitemap
        sitemap_urls = self.get_sitemap()

        post_process = lambda url: url
        if self.args.post_process:
            post_process = eval(self.args.post_process)

        post_process_sitemap = lambda url: url
        post_process_api = lambda url: url

        if self.args.post_process_sitemap:
            post_process_sitemap = eval(self.args.post_process_sitemap)

        if self.args.post_process_api:
            post_process_api = eval(self.args.post_process_api)

        schema_mapper = lambda url: url
        if self.https_to_http:
            schema_mapper = lambda url: re.sub(r'^https://(.*)', r'http://\1', url)

        if self.http_to_https:
            schema_mapper = lambda url: re.sub(r'^http://(.*)', r'https://\1', url)

        self.log.info("Post processing")
        # list of all urls as they are present in the page api, but post processed. Should be used for comparing, not for operations
        mapped_api_urls = list(map(lambda url: post_process(post_process_api(schema_mapper(url))), api_urls))

        mapped_file = self.file_in_target("mappeddata." + self.profile + ".api.txt")
        with io.open(mapped_file, 'w', encoding="utf-8") as f:
            f.write('\n'.join(sorted(mapped_api_urls)))
        # list of all urls as they are present in the sitemap, but post processed. Should be used for comparing, not for operations
        mapped_sitemap_urls = list(map(lambda url: post_process(post_process_sitemap(schema_mapper(url))), sitemap_urls))
        mapped_file = self.file_in_target("mappeddata." + self.profile + ".sitemap.txt")
        with io.open(mapped_file, 'w', encoding="utf-8") as f:
            f.write('\n'.join(sorted(mapped_sitemap_urls)))
        self.log.info(".")

        self.clean_from_api(
            mapped_api_urls,
            api_urls,
            mapped_sitemap_urls)

        self.add_to_api(
            mapped_api_urls,
            mapped_sitemap_urls,
            sitemap_urls)

        self.log.info("Ready.")



if __name__ == "__main__":
    CheckWithSitemap().main()
