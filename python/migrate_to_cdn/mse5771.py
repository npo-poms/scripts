
#!/usr/bin/env python3

import csv
import json
import os
import sys
from urllib.parse import urlparse

from npoapi import Binding, MediaBackend
from npoapi.data import ProgramTypeEnum, AvTypeEnum
from xsdata.formats.dataclass.serializers import JsonSerializer

from base import Base
import requests



class Process:


    def __init__(self, remove_files = True, start_at = 1, progress="mse5771.json"):
        self.api = MediaBackend().env('prod').command_line_client()
        self.logger = self.api.logger
        self.index = 0
        self.logger.info("Talking to %s" % (str(self.api)))
        self.remove_files = remove_files
        self.start_at = start_at
        self.progress_file = progress
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r", encoding="utf8") as file:
                self.progress = json.load(file)
        else:
            self.progress = dict()
        self.jsonserializer = JsonSerializer()

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
                url = r.headers['Location']

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


    def read_csv(self):
        count = 0
        with(open('walter.csv', 'r')) as file:
            reader = csv.reader(file)
            for row in reader:
                if 'VPRO' in row[2]:
                    original_url = row[13]
                    record = self.progress.get(original_url)
                    if record is None:
                        record = dict()
                        self.progress[original_url] = record


                    self.fix_url(original_url, record)
                    count +=1
        print(count)



Process().read_csv()
