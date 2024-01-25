import glob
import os
import subprocess
import time

import requests

from jproperties import Properties

p = Properties()
with open(os.path.expanduser('~') + "/conf/sourcingservice.properties", "rb") as f:
    p.load(f, "utf-8")
token = p["sourcingservice.audio.token"][0]
base_url = p["sourcingservice.audio.baseUrl"][0]

def upload_audio(mid: str, file: str):	
	st = time.time()

	response = requests.post("%s/api/ingest/%s/multipart-assetonly" % (base_url, mid), 
	              files={'upload_phase': (None, 'start'), 
	                     "email": (None, "m.meeuwissen.vpro@gmail.com"), 
	                     "file_size": (None, os.path.getsize(file))
	                     }, headers=headers())
	print("start", response.content)
	subprocess.call(['split', "-b", "10M", file, file + '.'])
	for f in sorted(glob.glob(file + '.*')):
		print(f)
		response = requests.post("%s/api/ingest/%s/multipart-assetonly" % (base_url, mid), 
	              files={'upload_phase': (None, 'transfer'), 
	                     'file_chunk': (os.path.basename(f), open(f, 'rb'))}, headers=headers())
		print(response.content)
		os.remove(f)
	response = requests.post("%s/api/ingest/%s/multipart-assetonly" % (base_url, mid), 
	              files={'upload_phase': (None, 'finish'), 
	                     }, headers=headers())
	print("finish", response.content)
	elapsed_time = time.time() - st
	print('Execution time:', elapsed_time, 'seconds')


				
		
def headers():
	return {'Authorization': "Bearer %s" % token}


upload_audio("WO_VPRO_A20025026", "/Users/michiel/samples/sample-big.mp3")