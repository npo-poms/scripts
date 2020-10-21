#!/usr/bin/env python3
import os
import re
import sys
import time
import urllib
from subprocess import Popen, PIPE
sys.path.append("..")
from check_with_sitemap import CheckWithSitemap

DEFAULT_JAVA_PATH = 'java'


class CheckWithSiteMapVpro(CheckWithSitemap):

    def __init__(self, java_path: str = DEFAULT_JAVA_PATH):
        super().__init__()
        self.jmx_url = self.args.jmx_url
        self.jmxterm_binary = ""
        self.java_path = java_path
        self._get_jmx_term_if_necessary()

    def add_arguments(self):
        super().add_arguments()
        api = self.api
        api.add_argument('--jmx_url', type=str, default=None, help='use JMX to trigger reindex')

    def perform_add_to_api(self, not_in_api: list):
        """Actually add to api"""

        if self.jmx_url:
            self.command = [self.java_path, '-jar', self.jmxterm_binary, '--url', self.jmx_url, "-n"]
            not_in_api = self._reindex_3voor12(not_in_api)
            not_in_api = self._reindex_mids(not_in_api)
            # todo:
            # - cinema

            self._reindex_urls(not_in_api)

        else:
            self.log.info("No jmx_url configured, not trying to implicetely add to api via JMX")

    def _reindex_mids(self, not_in_api: list) -> list:
        urls_with_mid = list(filter(lambda m: m[0] is not None, map(self._find_mid, not_in_api)))
        self.log.info("Reindexing %d mids" % len(urls_with_mid))
        page_size = 100
        for i in range(0, len(urls_with_mid), page_size):
            self._call_jmx_operation("nl.vpro.magnolia:name=IndexerMaintainerImpl", "reindexMediaObjects", list(map(lambda m : m[0], urls_with_mid[i: i + page_size])))

        urls = list(map(lambda u: u[1], urls_with_mid))
        return [e for e in not_in_api if e not in urls]

    def _reindex_3voor12(self, not_in_api: list) -> list:
        urls_with_uuids = list(filter(lambda m: m[0] is not None, map(self._find_update_uuid, not_in_api)))

        page_size = 100
        self.log.info("Reindexing %d updates" % len(urls_with_uuids))
        for i in range(0, len(urls_with_uuids), page_size):
            self._call_jmx_operation("nl.vpro.magnolia:name=DrieVoorTwaalfUpdateIndexer", "reindexUUIDs", list(map(lambda m : m[0], urls_with_uuids[i: i + page_size])))

        urls = list(map(lambda u: u[1], urls_with_uuids))
        return [e for e in not_in_api if e not in urls]

    def _reindex_urls(self, not_in_api: list) -> list:
        page_size = 20
        self.log.info("Reindexing %d urls" % len(not_in_api))
        for i in range(0, len(not_in_api), page_size ):
            self._call_jmx_operation("nl.vpro.magnolia:name=IndexerMaintainerImpl", "reindexUrls", not_in_api[i: i + page_size ])
        return not_in_api

    def _find_mid(self, url: str) -> list:
        matcher = re.match(".*?~(.*?)~.*", url)
        if matcher:
            return [matcher.group(1), url]
        else:
            return [None, url]

    def _find_update_uuid(self, url: str) -> list:
        matcher = re.match(".*?update~(.*?)~.*", url)
        if matcher:
            return [matcher.group(1), url]
        else:
            return [None, url]

    def _call_jmx_operation(self, bean: str, operation: str, sub_list: list):
        p = Popen(self.command, stdin=PIPE, stdout=PIPE, encoding='utf-8')
        out = p.communicate(input="bean " + bean  +"\nrun " + operation + " " + ",".join(sub_list))[0]
        self.log.info("output\n%s" % out)
        if "still busy" in out:
            self.log.info("Jmx reports that still busy. Let's wait a bit then")
            time.sleep(20)

    def _get_jmx_term_if_necessary(self):
        if self.jmx_url:
            jmxtermversion = "1.0.2"
            jmxterm = "jmxterm-" + jmxtermversion + "-uber.jar"
            path = os.path.dirname(os.path.realpath(__file__))
            self.jmxterm_binary = os.path.join(path, jmxterm)
            if not os.path.exists(self.jmxterm_binary):
                get_url = "https://github.com/jiaqi/jmxterm/releases/download/v" + jmxtermversion + "/" + jmxterm
                self.log.info("Downloading %s -> %s" % (get_url, self.jmxterm_binary))
                urllib.request.urlretrieve (get_url, self.jmxterm_binary)




if __name__ == "__main__":
    CheckWithSiteMapVpro().main()
