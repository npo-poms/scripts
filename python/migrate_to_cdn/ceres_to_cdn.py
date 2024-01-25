#!/usr/bin/env python3

import csv
import os
import subprocess
import sys

from npoapi import Binding
from npoapi.data import ProgramTypeEnum, AvTypeEnum

from base import Base


class Process(Base):

    def __init__(self, remove_files = True, start_at = 1):
        super().__init__(remove_files, start_at, progress="ceres.json")

    def scp_file(self, file:str, mid:str, record):
        if not 'dest' in record or not os.path.exists(record['dest']):
            self.logger.info("Scpin %s %s" % (mid, file))
            dest = '%s.asset' % (mid)
            if os.path.exists(dest + ".orig"):
                os.rename(dest + ".orig", dest)
            else:
                exit_code = subprocess.run(["scp", "vprosmc:" + file, dest])

            record.update({'dest': dest})
            self.save()
        else:
            self.logger.info("Nothing to download %s %s -> %s" % (mid, program_url, record['dest']))


    def process_files(self):
        total = 0
        skipped = 0
        ok = 0
        with (open("mid_filepath.txt", "r", encoding="utf_8") as input):
            while True:
                line = input.readline()
                if not line:
                    break
                (mid, file) = line.split(" ", 2)
                record = self.progress.get(mid, None)
                if record is None:
                    record = dict()
                    self.progress[mid] = record
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
                self.scp_file(file, mid, record)

                mo = self.api.get_full_object(mid, binding=Binding.XSDATA)
                self.logger.info("Mid %s, file %s -> %s" % (mid, file, str(mo)))
        self.logger.info("Total %d skipped %d ok %d" % (total, skipped, ok))



start_at = int(sys.argv[1]) if len(sys.argv) > 1 else 1

process = Process(remove_files=True, start_at = start_at)
process.process_files()

#process = Process(remove_files=False)
#record = dict()
#process.do_one("WO_VPRO_038831", record, "http://content.omroep.nl/vpro/poms/world/71/42/54/4/NPO_bb.m4v")
#process.logger.info(str(record))
