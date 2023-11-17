import csv
import json
import logging
import os
import subprocess
from dataclasses import asdict

import requests
from npoapi import MediaBackend

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


    def save(self):
        self.logger.info("Saving %d" % (len(self.progress)))
        with open("progress.saving.json", "w", encoding="utf8") as file:
            json.dump(self.progress, file, indent=2)
        os.replace("progress.saving.json", "progress.json")
        self.logger.info("Saved")



    def download_file(self, program_url:str, mid:str, record):
        if record.get("dest") is None:
            self.logger.info("Dowloading %s %s" % (mid, program_url))
            r = requests.get(program_url, allow_redirects=True)
            dest = '%s.asset' % (mid)
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
        media_info = record.get('media_info')
        if media_info is None:
            media_info = json.loads(subprocess.run(["/opt/homebrew/bin/mediainfo", "--Output=JSON", dest], stdout=subprocess.PIPE).stdout.decode('utf-8').strip())
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
        if bit_rate < 1_500_000:
            record.update({"reason": "%s Bitrate too low %s" % (mid, bit_rate)})
            return False
        if video_width < 768 or video_height < 432:
            record.update({"reason": "%s size %dx%d too small" % (mid, video_width, video_height)})
            return False
        aspect_ratio = video_width / video_height
        # min ratio 1.688889 or max ratio: 1.866667,
        if aspect_ratio < 1.688889 or aspect_ratio > 1.866667:
            record.update({"reason": "%s %dx%d aspect ratio (%f) out of range" % (mid, video_width, video_height, aspect_ratio)})
            return False
        if frame_rate < 20:
            record.update({"reason":  "%s frame rate too small:  %f" % (mid, frame_rate)})
            return False

        return True

    def fix_video_if_possible(self, record: dict):
        if record.get('fixed', 0) == 0:
            record['fixed'] = 0
            dest = record['dest']
            video_info = self.get_video_info(record)
            if video_info is None:
                return False
            video_bit_rate = int(video_info['BitRate'])
            frame_rate = float(video_info['FrameRate'])
            new_dest = dest + ".mp4"
            target_bit_rate = max(video_bit_rate, 2_000_000)
            args = ['ffmpeg', '-hide_banner' ,'-loglevel', 'info', '-y', '-i', dest,  '-q:a', '0', '-b:v', str(target_bit_rate), "-bufsize", "1500k"]
            if frame_rate < 25:
                target_frame_rate = 25
                args.extend(['-filter:v', "fps=%d" % target_frame_rate])

            args.append(new_dest)
            subprocess.call(args)
            if os.path.exists(new_dest):
                os.remove(dest)
                os.rename(new_dest, dest)
            record['fixed'] += 1
            self.save()

    def upload(self, mid: str, record:dict, mime_type:str):
        dest = record['dest']
        if record.get('result') is None:
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
                            continue

                    self.upload(mid, record, mime_type=avtype + '/' + ext)
                    self.remove_legacy(mid, program_url, record, publishstop=publish_stop)
                else:
                    self.logger.warning("Unknown action '%s' %s  %s" % (action, mid, program_url))

                    continue




process = Process()

process.process_csv()
