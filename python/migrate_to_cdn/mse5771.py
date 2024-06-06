#!/usr/bin/env python3

import csv
import dataclasses
import json
import logging
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timedelta

from npoapi import MediaBackend, Binding
from npoapi.data.media import Program, Segment, StreamingStatus
from xsdata.formats.dataclass.parsers import JsonParser
from xsdata.formats.dataclass.serializers import JsonSerializer
import requests

stop = '2023-11-01T12:00:00Z'


class Process:


    def __init__(self, remove_files = True, start_at = 1, progress="mse5771.json", dry_run=False, no_download=False, force_ss=False, endure_seconds=20):
        logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)-15s:%(levelname).3s:%(message)s")
        self.api = MediaBackend().env('prod').command_line_client()

        self.logger = self.api.logger
        if dry_run:
            self.logger.info("Dry run")
        if no_download:
            self.logger.info("No download")
        if force_ss:
            self.logger.info("Force streaming status")
        self.index = 0
        self.srcs_endure = timedelta(seconds=endure_seconds)
        self.last_upload = datetime.fromtimestamp(0)
        self.logger.info("Talking to %s" % (str(self.api)))
        self.remove_files = remove_files
        self.start_at = start_at
        self.no_download = no_download
        self.progress_file = progress
        self.dry_run = dry_run
        self.force_ss = force_ss
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r", encoding="utf8") as file:
                self.progress = json.load(file)
        else:
            self.progress = dict()
        self.jsonserializer = JsonSerializer()
        self.jsonparser = JsonParser()
        self.last_save = datetime.now()
        self.mids = []
        self.read_mids()

    def save(self, force = False):
        if not force and datetime.now() - self.last_save < timedelta(seconds=100):
            return
        self.last_save = datetime.now()
        with open(self.progress_file + ".saving", "w", encoding="utf8") as file:
            json.dump(self.progress, file, indent=2)
        os.replace(self.progress_file + ".saving", self.progress_file)
        self.logger.info("Saved %d" % (len(self.progress)))

    def fix_url(self, original_url, record):
        url = original_url
        if "status_code" not in record:
            while url.__contains__("radiobox"):
                r = requests.head(url, allow_redirects=False)
                headers = r.headers
                if 'Location' not in headers:
                    print("No location in " + url)
                    break
                url = headers['Location']

            fixed = url.replace("http://content.omroep.nl/", "https://mediastorage.omroep.nl/download/")
            fixed = fixed.replace("https://content.omroep.nl/", "https://mediastorage.omroep.nl/download/")
            fixed = fixed.replace("https://content.omroep.nl/", "https://mediastorage.omroep.nl/download/")
            fixed = fixed.replace("http://download.omroep.nl/", "https://mediastorage.omroep.nl/download/")
            fixed = fixed.replace("https://download.omroep.nl/", "https://mediastorage.omroep.nl/download/")
            r = requests.head(fixed)
            if r.status_code == 200:
                print(original_url + ' -> ' + url + ' -> ' + fixed)
            else:
                print(original_url + ' -> ' + url + ' -> ' + fixed + ' -> ' + str(r.status_code))
            record.update({"status_code": r.status_code})
            record.update({"fixed_url": fixed})
            self.save()
        else:
            self.logger.debug(record)

    def get_media(self, mid):
        if "mediaobjects" not in self.progress:
            self.progress["mediaobjects"] = dict()
        mediaobjects = self.progress["mediaobjects"]
        if mid not in mediaobjects:
            mediaobjects[mid] = self.jsonserializer.render(self.api.get_full_object(mid, binding=Binding.XSDATA))
            self.logger.info("Got %s" % mid)
            self.save()
        return

    def get_streaming_status(self, mid):
        if "streamingstati" not in self.progress:
            self.progress["streamingstati"] = dict()
        streaming_stati = self.progress["streamingstati"]
        if mid not in streaming_stati or self.force_ss:
            streaming_stati[mid] = self.jsonserializer.render(self.api.streaming_status(mid, binding=Binding.XSDATA))
            self.save()
        return self.jsonparser.decode(json.loads(streaming_stati[mid]), StreamingStatus)


    def needs_upload(self, mid):
        streaming_status = self.get_streaming_status(mid)
        if streaming_status is None:
            return True
        if streaming_status.withoutDrm.value == "ONLINE" or (streaming_status.audioWithoutDrm is not None and streaming_status.audioWithoutDrm.value == "ONLINE"):
            return False
        else:
            return True

    def get_xsdata(self, mid):
        mediaobjects = self.progress["mediaobjects"]
        load = json.loads(mediaobjects[mid])
        if load['type'] == 'SEGMENT':
            mo = self.jsonparser.decode(load, Segment)
        else:
            mo = self.jsonparser.decode(load, Program)

        return mo

    def download_file(self, mid, record: dict):
        if self.no_download:
            if 'dest' in record and not not os.path.exists('data/' + record['dest']):
                del record['dest']
                self.save()
        if not 'dest' in record or not os.path.exists('data/' + record['dest']):
            dest = '%s.asset' % (mid)
            self.logger.info("Downloading %s %s -> %s" % (mid, record['fixed_url'], dest))
            if os.path.exists('data/' + dest + ".orig"):
                os.rename('data/' + dest + ".orig", 'data/' + dest)
            else:
                r = requests.get(record['fixed_url'], allow_redirects=True)
                open('data/' + dest, 'wb').write(r.content)
            record.update({'dest': dest})
            self.save()
        else:
            self.logger.info("Nothing to download %s %s -> %s" % (mid, record['fixed_url'], record['dest']))

    def clean(self, mid, record):
        if 'dest' in record and os.path.exists('data/' + record['dest']):
            os.remove('data/' + record['dest'])
            self.logger.info("Removed %s" % record['dest'])
            if os.path.exists('data/' + record['dest'] + ".orig"):
                os.remove('data/' + record['dest'] + ".orig")
            del record['dest']
            self.save()



    def upload(self, mid, location, record):
        if 'upload_result' not in record:
            self.download_file(mid, record)
            if not self.dry_run and 'dest' in record:
                dest = record['dest']
                #self.logger.info("Uploading for %s %s %s" % (mid, dest, mime_type))
                delta = datetime.now() - self.last_upload
                if delta < self.srcs_endure:
                    sleep_time = self.srcs_endure - delta
                    self.logger.info("Sourcing service cannot endure over 1 req/%s. Waiting %d seconds" % (self.srcs_endure, sleep_time.total_seconds()))
                    time.sleep(sleep_time.total_seconds())
                self.last_upload = datetime.now()

                result = self.api.upload(mid, 'data/' + dest, content_type="audio/mp3", log=False)
                if dataclasses.is_dataclass(result):
                    record['upload_result'] = asdict(result)
                else:
                    record['upload_result'] = {"string": str(result)}
                self.logger.info(str(result))
                self.save()

                self.remove_legacy(mid, location, record)
                self.clean(mid, record)
        return record.get('upload_result')


    def remove_legacy(self, mid: str, location:str, record:dict, publishstop=stop):
        if not 'publishstop' in record:
            self.logger.info("Removing legacy %s %s" % (location, mid))
            self.api.set_location(mid, location, publishStop=publishstop, only_if_exists=True)
            record['publishstop'] = str(publishstop)
            self.save()

    def read_walter_csv(self, web_site = True):
        count = 0
        with(open('walter.csv', 'r')) as file:
            reader = csv.reader(file)
            for row in reader:
                mid = row[0]
                if web_site:
                    perform =  mid in self.mids
                else:
                    perform = 'VPRO' in row[2] or 'HUMA' in row[2] or 'NTR' in row[2]

                if perform:
                    count +=1
                    original_url = row[13]
                    self.process_record(mid, original_url)

        self.save(force=True)

        self.logger.info("Ready with walter csv %s (%s)" %(str(count), str(web_site)))


    def read_walter_csv_and_head(self):
        count = 0
        with(open('walter.csv', 'r')) as file:
            reader = csv.reader(file)
            for row in reader:
                mid = row[0]
                if mid == 'mid':
                    mid = "RBX_VPRO_6226969"
                entry_url = "https://entry.cdn.npoaudio.nl/handle/%s.mp3" %(mid)
                response = requests.head(entry_url)
                if response.status_code != 404:
                    self.logger.info("HEAD %s %s %s" % (mid, entry_url, response.status_code))
                count +=1
                if count % 1000 == 0:
                    self.logger.info("Processed %s" % count)



        self.logger.info("Ready with walter csv %s (%s)" %(str(count)))

    def read_podcast_csv(self):
        count = 0
        with(open('podcastitems.csv', 'r')) as file:
            reader = csv.reader(file)
            for row in reader:
                mid = row[0]
                if mid == 'mid':
                    continue
                original_url = row[1].split(" ")[0]
                if not original_url.startswith("http"):
                    self.logger.info("Skipping %s" % original_url)
                    continue
                count +=1
                self.process_record(mid, original_url)

        self.save(force=True)

        self.logger.info("Ready with podcast csv (%s)" %(str(count)))


    def process_record(self, mid, original_url):
        if not original_url.endswith(".mp3"):
            self.logger.info("Skipping %s" % original_url)
            return
        record = self.progress.get(original_url)
        if record is None:
            record = dict()
            self.progress[original_url] = record

        self.fix_url(original_url, record)

        #self.get_media( mid)
        if self.needs_upload(mid):
            self.upload(mid, original_url, record)
        else:
            self.clean(mid, record)


    def read_mids(self):
         with(open('website_media.csv', 'r')) as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) > 0:
                    mid = row[0]
                    self.mids.append(mid)
            self.logger.info("Read %d mids" % len(self.mids))


dryrun = "dryrun" in sys.argv
nodownload = "nodownload" in sys.argv
forcess = "forcess" in sys.argv


process = Process(dry_run=dryrun, no_download=nodownload, force_ss=forcess);
#process.read_podcast_csv()

#process.read_walter_csv(web_site=True)
#process.read_walter_csv(web_site=False)

process.read_walter_csv_and_head()
