#!/usr/bin/env python3

import csv
import json
import os
import subprocess
from dataclasses import asdict

import requests
from npoapi import MediaBackend, Binding
from xsdata.formats.dataclass.serializers import JsonSerializer

stop = '2023-11-01T12:00:00Z'
stop_video ='2123-11-01T12:00:00Z'

class Process:

    def __init__(self, broadcaster:str = 'vpro'):
        self.api = MediaBackend().env('prod').command_line_client()
        self.logger = self.api.logger
        self.index = 0
        self.logger.info("Talking to %s" % (str(self.api)))
        if os.path.exists("progress.json"):
            with open("progress.json", "r", encoding="utf8") as file:
                self.progress = json.load(file)
        else:
            self.progress = dict()
        self.jsonserializer =JsonSerializer()


    def save(self):
        self.logger.info("Saving %d" % (len(self.progress)))
        with open("progress.saving.json", "w", encoding="utf8") as file:
            json.dump(self.progress, file, indent=2)
        os.replace("progress.saving.json", "progress.json")
        self.logger.info("Saved")



    def download_file(self, program_url:str, mid:str, record):
        if not 'dest' in record or not os.path.exists(record['dest']):
            self.logger.info("Downloading %s %s" % (mid, program_url))
            dest = '%s.asset' % (mid)
            if os.path.exists(dest + ".orig"):
                os.rename(dest + ".orig", dest)
            else:
                r = requests.get(program_url, allow_redirects=True)
                open(dest, 'wb').write(r.content)
            record.update({'dest': dest})
            self.save()

    def probe(self, dest:str):
        ffprobe = sorted(subprocess.run(["ffprobe", "-loglevel", "error", "-show_entries", "stream=codec_type", "-of", "default=nw=1", dest], stdout=subprocess.PIPE).stdout.decode('utf-8').strip().split("\n"), reverse=True)
        if ffprobe[0] == "":
            return "failed", ""

        split = ffprobe[0].split("=")
        codec_type = split[1]
        return split[0], codec_type


    def get_video_info(self, record : dict):
        media_info = record['media_info']
        video_infos = list(filter(lambda e: e['@type'] == 'Video', media_info['media']['track']))
        if len(video_infos) == 0:
            record.update({"reason": "no video info found"})
            return None
        return video_infos[0]

    def check_video(self, mid, record: dict):
        dest = record.get('dest')
        media_info = json.loads(subprocess.run(["mediainfo", "--Output=JSON", dest], stdout=subprocess.PIPE).stdout.decode('utf-8').strip())
        record['media_info'] = media_info
        video_info = self.get_video_info(record)
        if video_info is None:
            return False
        video_bit_rate = int(video_info['BitRate'])
        video_height = int(video_info['Height'])
        video_width = int(video_info['Width'])
        audio_info = list(filter(lambda e: e['@type'] == 'Audio', media_info['media']['track']))
        audio_info_first = audio_info[0] if len(audio_info) > 0 else None
        if audio_info_first is not None:
            if "BitRate" in audio_info_first:
                audio_bit_rate = int(audio_info_first['BitRate'])
            elif 'BitRate_Nominal' in audio_info_first:
                audio_bit_rate = int(audio_info_first['BitRate_Nominal'])
            else:
                audio_bit_rate = 0
        else:
            audio_bit_rate = 0
        bit_rate = video_bit_rate + audio_bit_rate
        frame_rate = float(video_info['FrameRate'])
        reasons = []
        if bit_rate < 1_500_000:
            reasons.append({"reason": "%s Bitrate too low %s" % (mid, bit_rate), "reason_key": "bitrate"})
        if video_width < 768 or video_height < 432:
            reasons.append({"reason": "%s size %dx%d too small" % (mid, video_width, video_height), "reason_key": "size"})
        aspect_ratio = video_width / video_height
        # min ratio 1.688889 or max ratio: 1.866667,
        if aspect_ratio < 1.688889 or aspect_ratio > 1.866667:
            reasons.append({"reason": "%s %dx%d aspect ratio (%f) out of range" % (mid, video_width, video_height, aspect_ratio), "reason_key": "aspect_ratio"})
        if frame_rate < 20:
            reasons.append({"reason":  "%s frame rate too small:  %f" % (mid, frame_rate), "reason_key": "frame_rate"})
        record.update({"reasons": reasons})
        self.save()
        return len(reasons) == 0

    def fix_video_if_possible(self, record: dict):
        if record.get('fixed', 0) == 0:
            record['fixed'] = 0
            dest = record['dest']
            dest_orig = "%s.orig" % dest
            os.rename(dest, "%s.orig" % dest)
            video_info = self.get_video_info(record)
            if video_info is None:
                return False
            video_bit_rate = int(video_info['BitRate'])
            frame_rate = float(video_info['FrameRate'])
            new_dest = dest + ".mp4"
            target_bit_rate = max(video_bit_rate, 2_000_000)

            args = ['ffmpeg', '-hide_banner' ,'-loglevel', 'info', '-y', '-i', dest_orig,  '-q:a', '0', '-b:v', str(target_bit_rate), "-bufsize", "1500k"]
            if frame_rate < 25:
                target_frame_rate = 25
                args.extend(['-filter:v', "fps=%d" % target_frame_rate])

            reasons = record['reasons']
            if len(list(filter(lambda r: r['reason_key'] in ('size', 'aspect_ratio'), reasons))) > 0:
                video_height = max(432, int(video_info['Height']))
                video_width = max(768, int(video_info['Width']))
                args.extend(["-vf", "scale=%d:%d:force_original_aspect_ratio=increase,pad=%d:%d:-1:-1:color=black" %(video_width, video_height, video_width, video_height)])
            args.append(new_dest)
            subprocess.call(args)
            if os.path.exists(new_dest):
                os.rename(new_dest, dest)
                self.logger.info("Replaced %s with %s" % (dest, new_dest))
            record['fixed'] += 1
            record['ffmpeg'] = " ".join(args)
            self.save()

    def upload(self, mid: str, record:dict, mime_type:str):
        dest = record['dest']
        self.logger.info("Uploading for %s %s %s" % (mid, dest, mime_type))
        result = self.api.upload(mid, dest, content_type=mime_type, log=True)
        if isinstance(result, str):
            # video
            record['result'] = result
            success = True
        else:
            # audio
            record['result'] = asdict(result)
            success = result.status == "success"
        self.logger.info(str(result))
        self.save()

        self.logger.info("Uploading for %s %s %s" % (mid, dest, mime_type))

    def remove_legacy(self, mid: str, location:str, record:dict, publishstop=stop):
        if not 'publishstop' in record:
            self.logger.info("Removing legacy %s %s" % (location, mid))
            self.api.set_location(mid, location, publishStop=publishstop, only_if_exists=True)
            record['publishstop'] = str(publishstop)
            self.save()

    def streaming_status(self, mid:str, record):
        streaming_status = self.api.streaming_status(mid, binding=Binding.XSDATA)
        record['streaming_status'] = json.loads(self.jsonserializer.render(streaming_status))
        if streaming_status is None:
            return None
        if streaming_status.withoutDrm.value == "ONLINE" or (streaming_status.audioWithoutDrm is not None and streaming_status.audioWithoutDrm.value == "ONLINE"):
            return True
        else:
            return False

    def process_csv(self):
        with (open("Lagekwaliteitbronnenv1.csv", "r", encoding="utf_8_sig") as file):
            reader = csv.DictReader(file, delimiter=";")
            for row in reader:
                action = row['Voorgestelde Actie']
                program_url = row['program_url']
                mid = row['mid']
                record = self.progress.get(mid, None)
                if record is None:
                    record = dict()
                    self.progress[mid] = record
                if action == 'Delete':
                    self.logger.debug("Delete %s %s" % (mid, program_url))
                    continue
                if action == 'transcode & resize' or action == 'transcode' or action == 'resize' or action == 'resize & zwarte randen' or action == '':
                    self.logger.info(mid)
                    ss = self.streaming_status(mid, record)
                    self.logger.info("Streaming status %s %s" % (mid, str(record['streaming_status'])))
                    if ss is None:
                        self.logger("Skipped while getting streaming status %s" % (mid))
                        continue
                    if ss is True:
                        self.logger("Skipped while getting streaming status %s already true" % (mid))
                        continue
                    self.download_file(program_url, mid, record)
                    (a, avtype) = self.probe(record['dest'])
                    ext = os.path.splitext(program_url)[1][1:]
                    publish_stop = stop
                    if avtype == 'video':
                        publish_stop = stop_video
                        if not self.check_video(mid, record):
                            self.fix_video_if_possible(record)
                            if not self.check_video(mid, record):
                                self.logger.info("NOT OK %s %s" % (mid, program_url))
                                record.update({"skipped": "not ok"})
                                continue

                    self.upload(mid, record, mime_type=avtype + '/' + ext)
                    self.remove_legacy(mid, program_url, record, publishstop=publish_stop)
                    os.remove(record['dest'])
                else:
                    self.logger.warning("Unknown action '%s' %s  %s" % (action, mid, program_url))

                    continue




process = Process()

process.process_csv()