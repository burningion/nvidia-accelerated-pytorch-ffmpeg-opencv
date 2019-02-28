import subprocess
import glob
import random

filelist = glob.glob('*.mp4')

with open('/downloads/slices/filelist.txt', 'w') as f:
    for i in range(100):
        f.write("file %s\n" % random.choice(filelist))

f.close()
    
        
