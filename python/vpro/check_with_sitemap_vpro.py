#!/usr/bin/env python3
import os
import re
import sys
import urllib
from subprocess import Popen, PIPE
from typing import Optional
sys.path.append("..")
from check_with_sitemap import CheckWithSitemap


class CheckWithSiteMapVpro(CheckWithSitemap):

    def __init__(self):
        super().__init__()
        self.jmx_url = self.args.jmx_url
        self.jmxterm_binary = None
        self.get_jmx_term_if_necessary()

    def add_arguments(self):
        super().add_arguments()
        api = self.api
        api.add_argument('--jmx_url', type=str, default=None, help='use JMX to trigger reindex')

    def perform_add_to_api(self, not_in_api: list):
        """Actually add to api"""

        if self.jmx_url:
            command =  ["/usr/bin/java", '-jar', self.jmxterm_binary, '--url', self.jmx_url, "-n"]


            urls = list(filter(lambda  u : not self.find_mid(u), not_in_api))
            urls_page_size = 20
            for i in range(0, len(urls), urls_page_size ):
                sub_list = ",".join(urls[i: i + urls_page_size ])
                p = Popen(command, stdin=PIPE, stdout=PIPE, encoding='utf-8')
                out = p.communicate(input='bean nl.vpro.magnolia:name=IndexerMaintainerImpl\nrun reindexUrls "'+ sub_list + '"')
                self.log.info("output\n%s" % out[0])

            mids = list(filter(lambda m: m is not None, map(self.find_mid, not_in_api)))
            mids_page_size = 100
            for i in range(0, len(mids), mids_page_size):
                sub_list = ",".join(mids[i: i + mids_page_size])
                p = Popen(command, stdin=PIPE, stdout=PIPE, encoding='utf-8')
                out = p.communicate(input='bean nl.vpro.magnolia:name=IndexerMaintainerImpl\nrun reindexMediaObjects "'+ sub_list + '"')
                self.log.info("output\n%s" % out[0])

            # todo:
            # - cinema
            # - 3voor12 updates
        else:
            self.log.info("No jmx_url configured, not trying to implicetely add to api via JMX")

    def find_mid(self, url: str) -> Optional[str]:
        matcher = re.match(".*?~(.*?)~.*", url)
        if matcher:
            return matcher.group(1)
        else:
            return None

    def get_jmx_term_if_necessary(self):
        if self.jmx_url:
            jmxtermversion = "1.0.2"
            jmxterm = "jmxterm-" + jmxtermversion + "-uber.jar"
            path = os.path.dirname(os.path.realpath(__file__))
            jmxterm_binary = os.path.join(path, jmxterm)
            if not os.path.exists(jmxterm_binary):
                get_url = "https://github.com/jiaqi/jmxterm/releases/download/v" + jmxtermversion + "/" + jmxterm
                self.log.info("Downloading %s -> %s" % (get_url, jmxterm_binary))
                urllib.request.urlretrieve (get_url, jmxterm_binary)




if __name__ == "__main__":
    CheckWithSiteMapVpro().main()
