import subprocess
import requests
import shlex

import os

scraperURL = 'http://' + os.environ['SCRAPERAPP_SERVICE_HOST'] + ':' + os.environ['SCRAPERAPP_SERVICE_PORT']
req = requests.get(scraperURL + '/video-inference')
b = req.json()

counter = 0

for inference in b['inferences']:
    for i in range(len(inference['clock_segments'])):
        command = f"ffmpeg -i '{inference['filename']}' -ss {inference['clock_segments'][i]['start']} -t  {inference['clock_segments'][i]['length']} -c copy /downloads/slices/{counter:05d}.mp4"
        subprocess.call(shlex.split(command))
        counter += 1
