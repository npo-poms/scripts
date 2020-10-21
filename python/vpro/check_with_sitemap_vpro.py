#!/usr/bin/env python3
import os
import re
import sys
import urllib
from subprocess import Popen, PIPE
sys.path.append("..")
from check_with_sitemap import CheckWithSitemap


class CheckWithSiteMapVpro(CheckWithSitemap):

    def __init__(self):
        super().__init__()
        self.jmx_url = self.args.jmx_url
        self.jmxterm_binary = ""
        self._get_jmx_term_if_necessary()

    def add_arguments(self):
        super().add_arguments()
        api = self.api
        api.add_argument('--jmx_url', type=str, default=None, help='use JMX to trigger reindex')

    def perform_add_to_api(self, not_in_api: list):
        """Actually add to api"""

        if self.jmx_url:

            self.command = ["/usr/bin/java", '-jar', self.jmxterm_binary, '--url', self.jmx_url, "-n"]

            not_in_api = self._reindex_mids(not_in_api)
            # todo:
            # - cinema
            # - 3voor12 updates

            self._reindex_urls(not_in_api)

        else:
            self.log.info("No jmx_url configured, not trying to implicetely add to api via JMX")

    def _reindex_mids(self, not_in_api: list) -> list:
        urls_with_mid = list(filter(lambda m: m[0] is not None, map(self._find_mid, not_in_api)))
        self.log.info("Reindexing %d mids" % len(urls_with_mid))
        mids_page_size = 100
        for i in range(0, len(urls_with_mid), mids_page_size):
            sub_list = ",".join(list(map(lambda m : m[0], urls_with_mid[i: i + mids_page_size])))
            p = Popen(self.command, stdin=PIPE, stdout=PIPE, encoding='utf-8')
            out = p.communicate(input='bean nl.vpro.magnolia:name=IndexerMaintainerImpl\nrun reindexMediaObjects "'+ sub_list + '"')
            self.log.info("output\n%s" % out[0])

        urls = list(map(lambda u: u[1], urls_with_mid))
        return [e for e in not_in_api if e not in urls]

    def _reindex_urls(self, not_in_api: list) -> list:
        urls_page_size = 20
        self.log.info("Reindexing %d urls" % len(not_in_api))
        for i in range(0, len(not_in_api), urls_page_size ):
            sub_list = ",".join(not_in_api[i: i + urls_page_size ])
            p = Popen(self.command, stdin=PIPE, stdout=PIPE, encoding='utf-8')
            out = p.communicate(input='bean nl.vpro.magnolia:name=IndexerMaintainerImpl\nrun reindexUrls "'+ sub_list + '"')
            self.log.info("output\n%s" % out[0])
        return not_in_api

    def _find_mid(self, url: str) -> list:
        matcher = re.match(".*?~(.*?)~.*", url)
        if matcher:
            return [matcher.group(1), url]
        else:
            return [None, url]

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
