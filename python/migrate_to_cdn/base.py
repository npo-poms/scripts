#!/usr/bin/env python3

import json
import math
import os
import subprocess
import time
from datetime import datetime, timedelta

from dataclasses import asdict

import requests
from npoapi import MediaBackend, Binding
from xsdata.formats.dataclass.serializers import JsonSerializer

stop = '2023-11-01T12:00:00Z'
stop_video ='2123-11-01T12:00:00Z'


class Base:

    def __init__(self, remove_files = True, start_at = 1, progress="progress.json", socks=None, force_ss= False):
        self.api = MediaBackend().env('prod').command_line_client()
        self.logger = self.api.logger
        self.index = 0
        self.logger.info("Talking to %s" % (str(self.api)))
        self.remove_files = remove_files
        self.start_at = start_at
        self.progress_file = progress
        self.last_upload = datetime.fromtimestamp(0)
        self.srcs_endure = timedelta(minutes=1)
        self.proxies = socks is None and None or {"http": socks, "https": socks}
        self.force_ss = force_ss
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r", encoding="utf8") as file:
                self.progress = json.load(file)
        else:
            self.progress = dict()
        self.jsonserializer =JsonSerializer()

    def save(self):
        with open(self.progress_file + ".saving", "w", encoding="utf8") as file:
            json.dump(self.progress, file, indent=2)
        os.replace(self.progress_file + ".saving", self.progress_file)
        self.logger.info("Saved %d" % (len(self.progress)))


    def fix_url(self, original_url, record):
        url = original_url
        if "status_code" not in record:
            while url.__contains__("radiobox"):
                r = requests.head(url, allow_redirects=False, proxies=self.proxies)
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
            r = requests.head(fixed, proxies=self.proxies)
            if r.status_code == 200:
                print(original_url + ' -> ' + url + ' -> ' + fixed)
            else:
                print(original_url + ' -> ' + url + ' -> ' + fixed + ' -> ' + str(r.status_code))
            record.update({"status_code": r.status_code})
            record.update({"fixed_url": fixed})
            self.save()
        else:
            self.logger.debug(record)
        return record['fixed_url']

    def download_file(self, program_url:str, mid:str, record):
        if not 'dest' in record or not os.path.exists(record['dest']):
            self.logger.info("Downloading %s %s" % (mid, program_url))
            dest = '%s.asset' % (mid)
            if os.path.exists(dest + ".orig"):
                os.rename(dest + ".orig", dest)
            else:
                fixed = self.fix_url(program_url, record)
                r = requests.get(fixed, allow_redirects=True, proxies=self.proxies, timeout=10)
                open(dest, 'wb').write(r.content)
            self.logger.info("Dest %s with %d bytes" % (dest, os.path.getsize(dest)))
            record.update({'dest': dest})
            self.save()
        else:
            self.logger.info("Nothing to download %s %s -> %s" % (mid, program_url, record['dest']))

    @staticmethod
    def probe(dest:str):
        ffprobe = sorted(subprocess.run(["ffprobe", "-loglevel", "error", "-show_entries", "stream=codec_type", "-of", "default=nw=1", dest], stdout=subprocess.PIPE).stdout.decode('utf-8').strip().split("\n"), reverse=True)
        if ffprobe[0] == "":
            return "failed", ""

        split = ffprobe[0].split("=")
        codec_type = split[1]
        return split[0], codec_type


    def get_video_info(self, record : dict):
        media_info = record['media_info']
        media = media_info['media']
        if media is None:
            self.logger.info("No media in %s" % record)
            return None
        track = media['track'] if 'track' in media else None
        if track is None:
            self.logger.info("No track in %s" % record)
            return None
        video_infos = list(filter(lambda e: e['@type'] == 'Video', track))
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
            self.logger.info("No video info for %s" % mid)
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

    def convert_to_audio(self, record :dict):
        dest = record['dest']
        dest_orig = "%s.orig" % dest
        if not os.path.exists(dest_orig):
            os.rename(dest, dest_orig)
        args = ["ffmpeg", "-y", "-i", dest_orig, "-q:a", "0", "-map",  "a", "-f", "mp3", dest]
        record['ffmpeg'] = " ".join(args)
        subprocess.call(args)


    def fix_video_if_possible(self, record: dict):
        if record.get('fixed', 0) <= 1:
            if 'fixed' in record:
                record['fixed'] += 1
            else:
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

            reasons = record['reasons']

            if frame_rate < 25:
                target_frame_rate = 25
                self.logger.info("Scaling up frame rate %f -> %s " % (frame_rate, target_frame_rate))
            else:
                target_frame_rate = frame_rate

            video_options = "fps=%d" % target_frame_rate
            if len(list(filter(lambda r: r['reason_key'] in ('size', 'aspect_ratio'), reasons))) > 0:
                video_height = int(video_info['Height'])
                video_width = int(video_info['Width'])
                aspect_ratio = video_width / video_height
                if aspect_ratio > 16/9:
                    scaled_video_width = math.ceil(max(778, video_width))
                    scaled_video_height = math.ceil(scaled_video_width * 9 / 16)
                else:
                    scaled_video_height = math.ceil(max(432, video_height))
                    scaled_video_width = math.ceil(scaled_video_height * 16 / 9)

                # the bigger on
                video_options += ",scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:-1:-1:color=black" %(scaled_video_width, scaled_video_height, scaled_video_width, scaled_video_height)

            args.extend(["-vf", video_options])

            args.append(new_dest)
            self.logger.info("Running %s" % " ".join(args))
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
        delta = datetime.now() - self.last_upload
        if mime_type.startswith('audio'):
            if delta < self.srcs_endure:
                sleep_time = self.srcs_endure - delta
                self.logger.info("Sourcing service cannot endure over 1 req/%s. Waiting %d seconds" % (self.srcs_endure, sleep_time.total_seconds()))
                time.sleep(sleep_time.total_seconds())
            self.last_upload = datetime.now()

        result = self.api.upload(mid, dest, content_type=mime_type, log=False)
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
        return success

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

