import subprocess
import requests
import random
import os

scraperURL = 'http://' + os.environ['SCRAPERAPP_SERVICE_HOST'] + ':' + os.environ['SCRAPERAPP_SERVICE_PORT']

req = requests.get(f'{scraperURL}/snippets')
snippets = req.json()['snippets']

print(snippets)

def getUniqueVideo(vidlist, snippets):
    while True:
        vidCandidate = random.choice(snippets)
        if vidCandidate['video'] not in vidlist:
            return vidCandidate

with open('/downloads/slices/filelist.txt', 'w') as f:
    videoList = []

    # need at least 50 videos or we loop forever :)
    for i in range(50):
        video = getUniqueVideo(videoList, snippets)
        videoList.append(video['video'])
        f.write(f"file {video['filename']}\n")
f.close()
