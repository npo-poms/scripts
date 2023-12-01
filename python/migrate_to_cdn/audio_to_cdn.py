#!/usr/bin/env python3

import csv
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict

import requests
from npoapi import MediaBackend, Binding
from npoapi.data import ProgramTypeEnum, AvTypeEnum, PredictionUpdateType, Prediction, WorkflowEnumType
from xsdata.formats.dataclass.serializers import JsonSerializer

stop = '2023-11-01T12:00:00Z'

# \copy (select l.id, l.programurl, mid(l.mediaobject_id), onlinelocationurloverview(l.mediaobject_id), workflow(l.mediaobject_id)   from location l join mediaobject_broadcaster mb on l.mediaobject_id  = mb.mediaobject_id where l.workflow = 'PUBLISHED' and mb.broadcasters_id = 'VPRO' and (l.programurl like 'http%radiobox%' or l.programurl like 'http%content.omroep.nl%') order by l.mediaobject_id desc) to '/tmp/SYS-1258.csv' with delimiter E'\t' csv header;


#  See SYS-1258
class Process:

    def __init__(self, broadcaster:str = 'vpro'):
        self.api = MediaBackend().env('prod').command_line_client()
        self.logger = self.api.logger
        self.index = 0
        self.logger.info("Talking to %s" % (str(self.api)))
        self.jsonserializer = JsonSerializer()
        self.seen_mids = set()
        self.corrected = 0


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
        self.logger.info("Removing legacy %s %s %s" % (location, mid, stop))
        self.api.set_location(mid, location, publishStop=stop, only_if_exists=True)
        time.sleep(2) # avoid overfeeding the Consumer.Media.ws.RunAsMediaService queue

    def streaming_status(self, mid:str):
        streaming_status = self.api.streaming_status(mid, binding=Binding.XSDATA)
        if streaming_status is None:
            return None
        if streaming_status.withoutDrm.value == "ONLINE" or (streaming_status.audioWithoutDrm is not None and streaming_status.audioWithoutDrm.value == "ONLINE"):
            return True
        else:
            return False

    def remove_legacy_list(self, mid: str, overview:set):
        for l in overview:
            self.remove_legacy(mid, l)

    def check_streamingstatus(self, mid: str,  overview:set):
        if self.streaming_status(mid):
            full = self.api.get_full_object(mid)
            if full is None:
                self.logger.info("Not found object %s" % (mid))
                return False
            locations = full.locations.location if full.locations is not None else []
            found_entry = False
            need_remove = set()
            for location in locations:
                if location.programUrl.startswith("https://entry"):
                    found_entry = True
                if "radiobox" in location.programUrl or "content.omroep.nl" in location.programUrl:
                    if location.publishStop is None and location.workflow == WorkflowEnumType.PUBLISHED:
                        need_remove.add(location.programUrl)
            if found_entry:
                self.logger.info("Already online %s" % (mid))
                self.remove_legacy_list(mid, need_remove)
                return False
            else:
                self.logger.info("Online, but missing entry %s" % (mid))
                existing_prediction  = full.prediction[0] if len(full.prediction) else  None
                if existing_prediction is None:
                    self.logger.info("No prediction %s" % (mid))
                    return False
                else:
                    prediction = Prediction()
                    prediction.publishStart = existing_prediction.publishStart
                    prediction.publishStop = existing_prediction.publishStop
                    prediction.value = "INTERNETVOD"
                    result = self.api.post_prediction(mid, prediction)
                    self.logger.info("posted prediction %s-> %s" % (mid, result))
                    self.remove_legacy_list(mid, overview)
                    self.corrected += 1
                    return False

    def do_one(self, mid:str, programurl:str, overview:set = None):
        try:
            dest = self.download_file(programurl, mid)
        except Exception as e:
            self.logger.info("Download failed %s %s" % (mid, e))
            return False
        if dest is None:
            self.logger.info("Not downloadable %s" % (programurl))
            return False

        tries = 0
        while tries < 2:
            try:
                tries += 1
                result = self.upload(mid, 'audio/mp3', dest)
                self.logger.info("Upload result %s %s" % (mid, result))
                break
            except Exception as e:
                self.logger.info("Upload failed %s %s" % (mid, e))
                time.sleep(5)
                continue
        self.remove_legacy_list(mid, overview)
        os.remove(dest)

    def process_csv(self, ignore_until = 0):
        total = 0
        skipped = 0
        ok = 0

        with (open("SYS-1258.csv", "r", encoding="utf_8") as file):
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                total += 1
                if total <= ignore_until:
                    continue
                self.logger.info("%d Processing %s" % (total, row))
                mid = row['mid']

                if mid in self.seen_mids:
                    skipped += 1
                    self.logger.info("Mid already seen %s: %s" % (mid, programurl))
                    continue

                self.seen_mids.add(mid)
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

                if not self.check_streamingstatus(mid):
                    continue

                if not self.do_one(mid, programurl, overview):
                    continue
                ok += ok
        self.logger.info("Total %d skipped %d ok %d corrected %d" % (total, skipped, ok, self.corrected))




process = Process()

#process.process_csv(ignore_until= int(sys.argv[1]) if len(sys.argv) > 1 else 0)

process.do_one("5ee8ffebfc92c80f588ee2b2", "https://content.omroep.nl/nporadio/audio/34a076b3-08b3-4c0c-ae2e-33b5a04faf68/21e0312e-e04f-4b4a-8a20-d69d430699ec.mp3")
