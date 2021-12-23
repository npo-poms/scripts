#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import threading
import time
import urllib
from subprocess import Popen, PIPE

sys.path.append("..")
from check_with_sitemap import CheckWithSitemap

DEFAULT_JAVA_PATH = 'java'


class CheckWithSiteMapVpro(CheckWithSitemap):
    """
    This specialization is customized for VPRO.

    It can connect via JMX to VPRO's Mangolia CMS which contains the original pages, and request it to index missing pages

    This wraps a command line client for jmx: https://github.com/jiaqi/jmxterm/
    """

    def __init__(self, java_path: str = DEFAULT_JAVA_PATH):
        super().__init__()
        self.jmx_url = self.args.jmx_url
        self.jmxterm_binary = self.args.jmxterm_binary
        self.java_path = java_path
        self._get_jmx_term_if_necessary()
        if self.args.tunnel:
            tunnel = SshTunnel(self.log)
            tunnel.start()

    def add_arguments(self):
        super().add_arguments()
        api = self.api
        api.add_argument('--jmx_url', type=str, default=None, help='use JMX to trigger reindex. An url like "localhost:500" where this is tunneled to the magnolia backend server')
        api.add_argument('--jmxterm_binary', type=str, default=None, help='location of jmxterm binary')
        api.add_argument('--tunnel', action='store_true', default=False, help='set up jmx tunnel too')

    def perform_add_to_api(self, not_in_api: list):
        """
        Actually add to api
        """

        if self.jmx_url:
            self.jmxterm = [self.java_path, '-jar', self.jmxterm_binary, '--url', self.jmx_url, "-n", "-v", "silent"]

            not_in_api = self._reindex_3voor12(not_in_api)
            not_in_api = self._reindex_cinema_films(not_in_api)
            not_in_api = self._reindex_cinema_person(not_in_api)
            not_in_api = self._reindex_mids(not_in_api)

            self._reindex_urls(not_in_api)

        else:
            self.log.info("No jmx_url configured, not trying to implicitly add to api via JMX")

    def _reindex_mids(self, not_in_api: list) -> list:
        urls_with_mid = list(filter(lambda m: m[0] is not None, map(self._find_mid, not_in_api)))
        return self._reindex_ids(not_in_api, urls_with_mid, "nl.vpro.magnolia:name=IndexerMaintainerImpl", "reindexMediaObjects", 100,  "media objects")

    def _reindex_3voor12(self, not_in_api: list) -> list:
        urls_with_uuids = list(filter(lambda m: m[0] is not None, map(self._find_update_uuid, not_in_api)))
        return self._reindex_ids(not_in_api, urls_with_uuids, "nl.vpro.magnolia:name=DrieVoorTwaalfUpdateIndexer", "reindexUUIDs", 100,  "3voor12 updates")

    def _reindex_cinema_films(self, not_in_api: list) -> list:
        cinema_ids = list(filter(lambda m: m[0] is not None, map(self._find_cinema_film_id, not_in_api)))
        return self._reindex_ids(not_in_api, cinema_ids, "nl.vpro.magnolia:name=CinemaObjectIndexer", "reindex", 100,  "cinema films")

    def _reindex_cinema_person(self, not_in_api: list) -> list:
        cinema_ids = list(filter(lambda m: m[0] is not None, map(self._find_cinema_person_uid, not_in_api)))
        return self._reindex_ids(not_in_api, cinema_ids, "nl.vpro.magnolia:name=CinemaPersonIndexer", "reindex", 100,  "cinema persons")

    def _reindex_urls(self, not_in_api: list) -> None:
        page_size = 20
        self.log.info("Reindexing %d urls" % len(not_in_api))
        for i in range(0, len(not_in_api), page_size ):
            self._call_jmx_operation("nl.vpro.magnolia:name=IndexerMaintainerImpl", "reindexUrls", not_in_api[i: i + page_size ])

    def _find_mid(self, url: str) -> list:
        return self._find_by_regexp(".*?~(.*?)~.*", url)

    def _find_update_uuid(self, url: str) -> list:
        return self._find_by_regexp(".*?update~(.*?)~.*", url)

    def _find_cinema_film_id(self, url: str) -> list:
        return self._find_by_regexp(".*?film~(.*?)~.*", url)

    def _find_cinema_person_uid(self, url: str) -> list:
        return self._find_by_regexp(".*?persoon~(.*?)~.*", url)

    @staticmethod
    def _find_by_regexp(regex: str, url: str) -> list:
        matcher = re.match(regex, url)
        if matcher:
            return [matcher.group(1), url]
        else:
            return [None, url]

    def _reindex_ids(
            self, not_in_api: list,
            ids: list,
            bean: str,
            operation: str, page_size: int, name: str) -> list:
        self.log.info("Reindexing %d %s" % (len(ids), name))
        for i in range(0, len(ids), page_size):
            self._call_jmx_operation(bean, operation, list(map(lambda m : m[0], ids[i: i + page_size])))

        urls = list(map(lambda u: u[1], ids))
        self.log.debug("Associated with %s" % str(urls))
        return [e for e in not_in_api if e not in urls]


    def _call_jmx_operation(self, bean: str, operation: str, sub_list: list):
        p = Popen(self.jmxterm, stdin=PIPE, stdout=PIPE, encoding='utf-8')
        input = "bean " + bean  +"\nrun " + operation + " " + ",".join(sub_list)
        self.log.info("input\n%s" % input)
        out, error = p.communicate(input=input, timeout=100)
        self.log.info("output\n%s" % out)
        if error:
            self.log.info("error\n%s" % error)

        if "still busy" in out:
            self.log.info("Jmx reports that still busy. Let's wait a bit then")
            time.sleep(20)

    def _get_jmx_term_if_necessary(self):
        if self.jmx_url and not self.jmxterm_binary:
            from_env = os.getenv('JMXTERM_BINARY')
            if not from_env is None:
                self.jmxterm_binary=from_env
            else:
                jmxtermversion = "1.0.2"
                jmxterm = "jmxterm-" + jmxtermversion + "-uber.jar"
                path = os.path.dirname(os.path.realpath(__file__))
                self.jmxterm_binary = os.path.join(path, jmxterm)
                if not os.path.exists(self.jmxterm_binary):
                    get_url = "https://github.com/jiaqi/jmxterm/releases/download/v" + jmxtermversion + "/" + jmxterm
                    self.log.info("Downloading %s -> %s" % (get_url, self.jmxterm_binary))
                    urllib.request.urlretrieve (get_url, self.jmxterm_binary)

class SshTunnel(threading.Thread):
    def __init__(self, log):
        threading.Thread.__init__(self)
        self.daemon = True              # So that thread will exit when
                                        # main non-daemon thread finishes
        self.log = log

    def run(self):
        self.log.info("Setting up tunnel")
        if subprocess.call([
            'ssh', '-N', '-4',
                   '-L', '5000:localhost:5000',
                   'os2-magnolia-backend-prod-01'
                ]):
            raise Exception ('ssh tunnel setup failed')



if __name__ == "__main__":
    CheckWithSiteMapVpro().main()
