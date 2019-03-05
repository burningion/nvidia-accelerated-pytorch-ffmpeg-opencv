import subprocess
import requests
import shlex

import uuid

import os

scraperURL = 'http://' + os.environ['SCRAPERAPP_SERVICE_HOST'] + ':' + os.environ['SCRAPERAPP_SERVICE_PORT']
req = requests.get(scraperURL + '/video-inference')
b = req.json()

counter = 0

def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def getHrMinSec(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '{:d}:{:02d}:{:02d}'.format(h, m, s)

for inference in b['inferences']:
    for i in range(len(inference['clock_segments'])):
        r = requests.get(f'{scraperURL}/snippets?video_id={inference["video_id"]}&start={inference["clock_segments"][i]["start"]}')
        exists = r.json()

        if len(exists.values()) > 0:
            print('Skipping existing snippet')
            continue

        length = getHrMinSec(10)

        filename = uuid.uuid4()
        if get_sec(inference['clock_segments'][i]['length']) >= 10:
            length = getHrMinSec(10)
        else:
            length = inference['clock_segments'][i]['length']
        if inference['filename'][-4:] == 'webm':
            command = f"ffmpeg -hwaccel cuvid -c:v vp8_cuvid -i '{inference['filename']}' -ss {inference['clock_segments'][i]['start']} -t {length} -f mp4 -filter:v scale_npp=w=1280:h=720:format=yuv420p:interp_algo=lanczos -c:v h264_nvenc -preset slow -acodec aac -r 30 /downloads/slices/{filename}.mp4 -hide_banner"
        else:
            command = f"ffmpeg -hwaccel cuvid -c:v h264_cuvid -i '{inference['filename']}' -ss {inference['clock_segments'][i]['start']} -t {length} -f mp4 -filter:v scale_npp=w=1280:h=720:format=yuv420p:interp_algo=lanczos -c:v h264_nvenc -preset slow -acodec aac -r 30 /downloads/slices/{filename}.mp4 -hide_banner"
        subprocess.call(shlex.split(command))

        snippet = {'filename': f'{filename}.mp4',
                   'snippet_type': 'clock',
                   'start': f"{inference['clock_segments'][i]['start']}",
                   'duration': f"{length}",
                   'video_id': f'{inference["video_id"]}'}
        r = requests.post(f'{scraperURL}/snippets', json=snippet)
        counter += 1
