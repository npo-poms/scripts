#!/usr/bin/env python3

import csv
import json
import os
import subprocess
from dataclasses import asdict

import requests
from npoapi import MediaBackend, Binding
from npoapi.data import ProgramTypeEnum, AvTypeEnum, PredictionUpdateType, Prediction
from xsdata.formats.dataclass.serializers import JsonSerializer

stop = '2023-11-01T12:00:00Z'


class Process:

    def __init__(self, broadcaster:str = 'vpro'):
        self.api = MediaBackend().env('prod').command_line_client()
        self.logger = self.api.logger
        self.index = 0
        self.logger.info("Talking to %s" % (str(self.api)))
        self.jsonserializer = JsonSerializer()



    def download_file(self, program_url:str, mid:str):
        self.logger.info("Downloading %s %s" % (mid, program_url))
        dest = '%s.asset' % (mid)
        r = requests.get(program_url, allow_redirects=True)
        if r.status_code != 200:
            self.logger.error("Could not download %s %s" % (mid, program_url))
            return None
        open(dest, 'wb').write(r.content)
        return dest

    def upload(self, mid: str, mime_type:str, dest:str):
        self.logger.info("Uploading for %s %s %s" % (mid, dest, mime_type))
        result = self.api.upload(mid, dest, content_type=mime_type, log=False)
        result_as_dict = asdict(result)
        success = result.status == "success"
        self.logger.info(str(result))
        return success

    def remove_legacy(self, mid: str, location:str):
        self.logger.info("Removing legacy %s %s" % (location, mid))
        self.api.set_location(mid, location, publishStop=stop, only_if_exists=True)

    def streaming_status(self, mid:str):
        streaming_status = self.api.streaming_status(mid, binding=Binding.XSDATA)
        if streaming_status is None:
            return None
        if streaming_status.withoutDrm.value == "ONLINE" or (streaming_status.audioWithoutDrm is not None and streaming_status.audioWithoutDrm.value == "ONLINE"):
            return True
        else:
            return False

    def remove_legacy_list(self, mid: str, overview:list):
        for l in overview:
            pu = l.split(" ")[0]
            if "radiobox" in pu or "content.omroep.nl" in pu:
                self.remove_legacy(mid, pu)

    def process_csv(self):
        total = 0
        skipped = 0
        ok = 0
        corrected = 0
        with (open("SYS-1258.csv", "r", encoding="utf_8") as file):
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                self.logger.info("Processing %s" % (row))
                mid = row['mid']
                total += 1

                programurl = row['programurl']
                if not programurl.endswith(".mp3"):
                    skipped += 1
                    self.logger.info("Not mp3 %s: %s" % (mid, programurl))
                    continue

                workflow = row['workflow']
                if not workflow == "PUBLISHED":
                    self.logger.info("Not published %s" % (mid))
                    skipped += 1
                    continue

                overview = eval(row['onlinelocationurloverview'])
                if self.streaming_status(mid):
                    full = self.api.get_full_object(mid)
                    locations = full.locations.location
                    found_entry = False
                    for location in locations:
                        if location.programUrl.startswith("https://entry"):
                            found_entry = True
                    if found_entry:
                        skipped += 1
                        self.logger.info("Already online %s" % (mid))
                        continue
                    else:
                        self.logger.info("Online, but missing entry %s" % (mid))
                        existing_prediction  = full.prediction[0] if len(full.prediction) else  None
                        if existing_prediction is None:
                            self.logger.info("No prediction %s" % (mid))
                            skipped += 1
                            continue
                        else:
                            prediction = Prediction()
                            prediction.publishStart = existing_prediction.publishStart
                            prediction.publishStop = existing_prediction.publishStop
                            prediction.value = "INTERNETVOD"
                            result = self.api.post_prediction(mid, prediction)
                            self.logger.info("posted prediction %s-> %s" % (mid, result))
                            self.remove_legacy_list(mid, overview)
                            corrected += 1
                            continue


                dest = self.download_file(programurl, mid)
                if dest is None:
                    self.logger.info("Not downloadable %s" % (programurl))
                    skipped += 1
                    continue


                self.upload(mid, 'audio/mp3', dest)
                self.remove_legacy_list(mid, overview)
                os.remove(dest)
                ok += ok
        self.logger.info("Total %d skipped %d ok %d corrected %d" % (total, skipped, ok, corrected))




process = Process()

process.process_csv()
