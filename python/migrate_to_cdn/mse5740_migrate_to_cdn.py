#!/usr/bin/env python3

import csv
import os
import sys
from datetime import timedelta

from npoapi import Binding
from npoapi.data import ProgramTypeEnum, AvTypeEnum

from base import Base

stop = '2023-11-01T12:00:00Z'
stop_video ='2123-11-01T12:00:00Z'


class Process(Base):

    def do_one(self, mid:str, record: dict, program_url:str):
        mo = self.api.get_full_object(mid, binding=Binding.XSDATA)

        if mo is None:
            record.update({"skipped": "not exists"})
            self.save()
            return False

        if self.streaming_status(mid, record):
            record.update({"skipped": "already uploaded"})
            self.logger.info("Already uploaded %s" % mid)
            self.save()
            return False
        self.download_file(program_url, mid, record)
        (a, avtype) = self.probe(record['dest'])
        ext = os.path.splitext(program_url)[1][1:]
        publish_stop = stop
        if avtype == 'video':
            publish_stop = stop_video
            if not self.check_video(mid, record):
                self.fix_video_if_possible(record)
                if not self.check_video(mid, record):
                    if mo.avType == AvTypeEnum.AUDIO:
                        self.convert_to_audio(record)
                        ext = 'mp3'
                        avtype = 'audio'
                        self.logger.info("%s %s: %s. Progressing as audio" % (mid, program_url, avtype))
                        self.save()
                    else:
                        self.logger.info("NOT OK %s %s" % (mid, program_url))
                        record.update({"skipped": "not ok"})
                        if self.remove_files:
                            os.remove(record['dest'])
                        self.save()
                        return False
                else:
                    ext = 'mp4'
                    self.logger.info("%s %s: %s. Successfully fixed. Processing video" % (mid, program_url, avtype))

        else:
            if mo.avType == AvTypeEnum.AUDIO:
                self.logger.info("%s %s: %s. Progressing as audio" % (mid, program_url, avtype))
                avtype = 'audio'
                ext = 'mp3'
            else:
                self.logger.info("NOT OK %s %s " % (mid, program_url))
                return False


        success = self.upload(mid, record, mime_type=avtype + '/' + ext)
        if success:
            self.remove_legacy(mid, program_url, record, publishstop=publish_stop)
            if self.remove_files:
                os.remove(record['dest'])
                if os.path.exists(record['dest'] + ".orig"):
                   os.remove(record['dest'] + ".orig")
        else:
            self.logger.warn("Could not upload")
        return True

    def process_csv(self):
        total = 0
        skipped = 0
        ok = 0
        with (open("mse5740_vpro.csv", "r", encoding="utf_8_sig") as file):
            reader = csv.DictReader(file, delimiter=",")
            for row in reader:
                mid = row['mid']
                overview = row['onlinelocationoverview']
                programurl = row['programurl']
                if "PREPR" in mid:
                    continue
                if overview != '{MP3}':
                    continue
                self.logger.info("Considering %s %s" % (mid, overview))
                record = self.progress.get(mid, None)
                if record is None:
                    record = dict()
                    self.progress[mid] = record
                total += 1
                self.do_one(mid, record, programurl)
        self.logger.info("Total %d skipped %d ok %d" % (total, skipped, ok))



start_at = int(sys.argv[1]) if len(sys.argv) > 1 else 1

process = Process(remove_files=True, start_at = start_at, progress="mse5740_progress.json")
process.srcs_endure = timedelta(seconds=30)
process.process_csv()

#process = Process(remove_files=False)
#record = dict()
#process.do_one("WO_VPRO_038831", record, "http://content.omroep.nl/vpro/poms/world/71/42/54/4/NPO_bb.m4v")
#process.logger.info(str(record))
