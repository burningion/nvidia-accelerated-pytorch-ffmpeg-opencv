from bs4 import BeautifulSoup as bs
from pytube import YouTube
import requests

base = "https://www.youtube.com/results?search_query="
query = "clock,creativecommons"

r = requests.get(base + query)
page = r.text

soup = bs(page, 'html.parser')
vids = soup.findAll('a',attrs={'class':'yt-uix-tile-link'})

videolist =[]
for v in vids:
    tmp = 'https://www.youtube.com' + v['href']
    videolist.append(tmp)

print("Found and downloading %i videos" % len(videolist))

for item in videolist:
    YouTube(item).streams.first().download()
