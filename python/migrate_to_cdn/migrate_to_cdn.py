#!/usr/bin/env python3

import csv
import os
import sys

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
            return  False
        if mo.typeValue == ProgramTypeEnum.BROADCAST:
            record.update({"skipped": "may not upload broadcast"})
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
                        self.logger.info("NOT OK %s %s -> %s" % (mid, program_url, str(record['reasons'])))
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
                self.logger.info("NOT OK %s %s -> %s" % (mid, program_url, str(record['reasons'])))
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
        with (open("Lagekwaliteitbronnenv1.csv", "r", encoding="utf_8_sig") as file):
            reader = csv.DictReader(file, delimiter=";")
            for row in reader:
                action = row['Voorgestelde Actie']
                program_url = row['program_url']
                mid = row['mid']
                record = self.progress.get(mid, None)
                total += 1
                if total < self.start_at:
                    continue
                if record is None:
                    record = dict()
                    self.progress[mid] = record
                if action == 'Delete':
                    self.logger.debug("Delete %s %s" % (mid, program_url))
                    continue
                if action == 'transcode & resize' or action == 'transcode' or action == 'resize' or action == 'resize & zwarte randen' or action == '':
                    self.logger.info(mid)
                    ss = self.streaming_status(mid, record)
                    self.logger.info("%d Streaming status %s %s" % (total, mid, str(record['streaming_status'])))
                    if ss is None:
                        self.logger.info("Skipped while getting streaming status %s" % (mid))
                        skipped += 1
                        continue
                    if ss is True:
                        self.logger.info("Skipped while getting streaming status %s already true" % (mid))
                        ok += 1
                        continue
                    try:
                        if self.do_one(mid, record, program_url):
                            ok += 1
                        else:
                            skipped += 1
                    except Exception as e:
                        self.logger.warning("%d Exception %s %s" % (total, mid, str(e)))
                        record['exception'] = str(e)
                    self.save()
                else:
                    self.logger.warning("%d Unknown action '%s' %s  %s" % (total, action, mid, program_url))

                    continue
        self.logger.info("Total %d skipped %d ok %d" % (total, skipped, ok))



start_at = int(sys.argv[1]) if len(sys.argv) > 1 else 1

process = Process(remove_files=True, start_at = start_at)
process.process_csv()

#process = Process(remove_files=False)
#record = dict()
#process.do_one("WO_VPRO_038831", record, "http://content.omroep.nl/vpro/poms/world/71/42/54/4/NPO_bb.m4v")
#process.logger.info(str(record))
