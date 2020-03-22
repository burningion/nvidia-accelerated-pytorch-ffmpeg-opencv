import cv2
import numpy as np
import os

def make_edges(image, frameno, videofile):
    edges = cv2.Canny(image,100,200)
    plt.imsave(os.path.join("/pfs/out", f"{videofile}-{frameno:09}.png"), edges, cmap = 'gray')

for dirpath, dirs, files in os.walk("/pfs/videos"):
    for filename in files:
        cap = cv2.VideoCapture(filename)
        assert cap.isOpened(), 'Cannot capture source'
        tail = os.path.split(filename)[1]
        videofile = os.path.splitext(tail)[0]
        frames = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frameno += 1
                make_edges(frame, frameno, videofile)
