#!/usr/bin/env python3

import csv
import json
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


    def __init__(self, remove_files = True, start_at = 1, progress="mse5771.json", dryrun=False):
        self.api = MediaBackend().env('prod').command_line_client()
        self.logger = self.api.logger
        self.index = 0
        self.srcs_endure = timedelta(seconds=30)
        self.last_upload = datetime.fromtimestamp(0)
        self.logger.info("Talking to %s" % (str(self.api)))
        self.remove_files = remove_files
        self.start_at = start_at
        self.progress_file = progress
        self.dry_run = dryrun
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r", encoding="utf8") as file:
                self.progress = json.load(file)
        else:
            self.progress = dict()
        self.jsonserializer = JsonSerializer()
        self.jsonparser = JsonParser()

    def save(self):
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
            print(record)

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
        if mid not in streaming_stati:
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

    def download_file(self, mid, record):
        if not 'dest' in record or not os.path.exists('data/' + record['dest']):
            dest = '%s.asset' % (mid)
            self.logger.info("Downloading %s %s -> %s" % (mid, record['fixed_url'], dest))
            if os.path.exists('data/' + dest + ".orig"):
                os.rename('data/' + dest + ".orig", 'data/' + dest)
            else:
                r = requests.get(record['fixed_url'], allow_redirects=True)
                open(dest, 'wb').write(r.content)
            record.update({'dest': dest})
            self.save()
        else:
            self.logger.info("Nothing to download %s %s -> %s" % (mid, record['fixed_url'], record['dest']))


    def upload(self, mid, location, record):
        if 'upload_result' not in record:
            self.download_file(mid, record)
            if not self.dry_run:
                dest = record['dest']
                #self.logger.info("Uploading for %s %s %s" % (mid, dest, mime_type))
                delta = datetime.now() - self.last_upload
                if delta < self.srcs_endure:
                    sleep_time = self.srcs_endure - delta
                    self.logger.info("Sourcing service cannot endure over 1 req/%s. Waiting %d seconds" % (self.srcs_endure, sleep_time.total_seconds()))
                    time.sleep(sleep_time.total_seconds())
                self.last_upload = datetime.now()

                result = self.api.upload(mid, 'data/' + dest, content_type="audio/mp3", log=False)
                record['upload_result'] = asdict(result)
                success = result.status == "success"
                self.logger.info(str(result))
                self.save()

                self.remove_legacy(mid, location, record)
        return record.get('upload_result')


    def remove_legacy(self, mid: str, location:str, record:dict, publishstop=stop):
        if not 'publishstop' in record:
            self.logger.info("Removing legacy %s %s" % (location, mid))
            self.api.set_location(mid, location, publishStop=publishstop, only_if_exists=True)
            record['publishstop'] = str(publishstop)
            self.save()

    def read_csv(self):
        count = 0
        with(open('walter.csv', 'r')) as file:
            reader = csv.reader(file)
            for row in reader:
                if 'VPRO' in row[2] or 'HUMAN' in row[2]:
                    count +=1
                    original_url = row[13]
                    record = self.progress.get(original_url)
                    if record is None:
                        record = dict()
                        self.progress[original_url] = record

                    self.fix_url(original_url, record)
                    mid = row[0]
                    #self.get_media( mid)
                    if self.needs_upload(mid):
                        self.upload(mid, original_url, record)



        print(count)

dryrun = "dryrun" in sys.argv

Process(dryrun=dryrun).read_csv()
