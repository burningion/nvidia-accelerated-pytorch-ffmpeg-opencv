from __future__ import division
import IPython
import time
import torch 
import torch.nn as nn
from torch.autograd import Variable
import numpy as np
import cv2 
from util import *
from darknet import Darknet
from preprocess import prep_image, inp_to_image, letterbox_image
import pandas as pd
import random 
import pickle as pkl
import argparse

import requests

from ddtrace import tracer, patch_all
from ddtrace.context import Context

try:
    tracer.configure(
    hostname=os.environ['DD_AGENT_SERVICE_HOST'],
    port=os.environ['DD_AGENT_SERVICE_PORT']
)

except:
    print("No environment variables for Datadog set. App won't be instrumented.")

patch_all()

def get_test_input(input_dim, CUDA):
    img = cv2.imread("dog-cycle-car.png")
    img = cv2.resize(img, (input_dim, input_dim)) 
    img_ =  img[:,:,::-1].transpose((2,0,1))
    img_ = img_[np.newaxis,:,:,:]/255.0
    img_ = torch.from_numpy(img_).float()
    img_ = Variable(img_)
    
    if CUDA:
        img_ = img_.cuda()
    
    return img_

def prep_image(img, inp_dim):
    """
    Prepare image for inputting to the neural network. 
    
    Returns a Variable 
    """

    orig_im = img
    dim = orig_im.shape[1], orig_im.shape[0]
    img = (letterbox_image(orig_im, (inp_dim, inp_dim)))
    img_ = img[:,:,::-1].transpose((2,0,1)).copy()
    img_ = torch.from_numpy(img_).float().div(255.0).unsqueeze(0)
    return img_, orig_im, dim

def write(x, img, frame_no):
    c1 = tuple(x[1:3].int())
    c2 = tuple(x[3:5].int())
    cls = int(x[-1])
    label = "{0}".format(classes[cls])
    if label == 'clock':
        print("Clock at frame %i" % frame_no)
        #  int(x[-1]) == 74
    color = random.choice(colors)
    cv2.rectangle(img, c1, c2,color, 1)
    t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1 , 1)[0]
    c2 = c1[0] + t_size[0] + 3, c1[1] + t_size[1] + 4
    cv2.rectangle(img, c1, c2,color, -1)
    cv2.putText(img, label, (c1[0], c1[1] + t_size[1] + 4), cv2.FONT_HERSHEY_PLAIN, 1, [225,255,255], 1);
    return img

def extract_markers(result):
    c1 = tuple(result[1:3].int())
    c2 = tuple(result[3:5].int())
    cls = int(result[-1])
    label = "{0}".format(classes[cls])
    return {'x': int(c1[0]), 'y': int(c1[1]), 'h': int(c2[0]), 'w': int(c2[1]), 'type': label}

def arg_parse():
    """
    Parse arguements to the detect module
    
    """
    
    
    parser = argparse.ArgumentParser(description='YOLO v3 Video Detection Module')
   
    parser.add_argument("--video", dest = 'video', help = 
                        "Video to run detection upon",
                        default = "video.avi", type = str)
    parser.add_argument("--dataset", dest = "dataset", help = "Dataset on which the network has been trained", default = "pascal")
    parser.add_argument("--confidence", dest = "confidence", help = "Object Confidence to filter predictions", default = 0.5)
    parser.add_argument("--nms_thresh", dest = "nms_thresh", help = "NMS Threshhold", default = 0.4)
    parser.add_argument("--cfg", dest = 'cfgfile', help = 
                        "Config file",
                        default = "cfg/yolov3.cfg", type = str)
    parser.add_argument("--weights", dest = 'weightsfile', help = 
                        "weightsfile",
                        default = "yolov3.weights", type = str)
    parser.add_argument("--reso", dest = 'reso', help = 
                        "Input resolution of the network. Increase to increase accuracy. Decrease to increase speed",
                        default = "416", type = str)
    parser.add_argument("--frame-image", dest="image", default=False, help="Save image of detected frame", type=bool)
    parser.add_argument("--frame-skip", dest="skip", default=1, help="Skip N number of detected frames", type=int)
    parser.add_argument("--post-url", dest="post_url", help="URL to POST JSON back to")
    parser.add_argument("--trace-id", dest="trace_id", help="Trace ID")
    parser.add_argument("--parent-id", dest="parent_id", help="Parent Trace ID")
    parser.add_argument("--sampling-priority", dest="sampling_priority", help="Trace Sampling Priority")
    return parser.parse_args()


def create_context(trace_id, span_id, priority):
    return Context(trace_id=trace_id, span_id=span_id, sampling_priority=priority)

if __name__ == '__main__':
    args = arg_parse()
    span = tracer.trace("web.request", service="yolo-inference-process")
    if args.trace_id:
        context = create_context(args.trace_id, args.parent_id, args.sampling_priority)
        tracer.context_provider.activate(context)
    confidence = float(args.confidence)
    nms_thesh = float(args.nms_thresh)
    start = 0

    CUDA = torch.cuda.is_available()

    num_classes = 80

    
    bbox_attrs = 5 + num_classes
    
    print("Loading network.....")
    model = Darknet(args.cfgfile)
    model.load_weights(args.weightsfile)
    print("Network successfully loaded")

    model.net_info["height"] = args.reso
    inp_dim = int(model.net_info["height"])
    assert inp_dim % 32 == 0 
    assert inp_dim > 32

    if CUDA:
        model.cuda()
        print("Using cuda!")
    
    model(get_test_input(inp_dim, CUDA), CUDA)

    model.eval()
    
    videofile = args.video

    print(args.image)
    cap = cv2.VideoCapture(videofile)
    videoData = {'video_file': args.video, 'frame_data': [], 'fps': cap.get(cv2.CAP_PROP_FPS)}

    #fourcc = cv2.VideoWriter_fourcc(*'X265') # invalid fourcc, but it forces GPU usage for me *shrug*
    #out = cv2.VideoWriter('train.avi',fourcc, 30.0, (480,360))
    assert cap.isOpened(), 'Cannot capture source'
    
    frames = 0
    frameDetected = -1
    framesOut = 1
    start = time.time()    
    while cap.isOpened():
        
        ret, frame = cap.read()
        if ret:
            

            img, orig_im, dim = prep_image(frame, inp_dim)
            
            im_dim = torch.FloatTensor(dim).repeat(1,2)                        
            
            
            if CUDA:
                im_dim = im_dim.cuda()
                img = img.cuda()
            
            with torch.no_grad():   
                output = model(Variable(img), CUDA)
            output = write_results(output, confidence, num_classes, nms = True, nms_conf = nms_thesh)

            if type(output) == int:
                frames += 1
                continue
                #print("FPS of the video is {:5.2f}".format( frames / (time.time() - start)))
                '''
                cv2.imshow("frame", orig_im)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    break
                continue
                '''
                #out.write(orig_im)
            
            

            
            im_dim = im_dim.repeat(output.size(0), 1)
            scaling_factor = torch.min(inp_dim/im_dim,1)[0].view(-1,1)
            
            output[:,[1,3]] -= (inp_dim - scaling_factor*im_dim[:,0].view(-1,1))/2
            output[:,[2,4]] -= (inp_dim - scaling_factor*im_dim[:,1].view(-1,1))/2
            
            output[:,1:5] /= scaling_factor
    
            for i in range(output.shape[0]):
                output[i, [1,3]] = torch.clamp(output[i, [1,3]], 0.0, im_dim[i,0])
                output[i, [2,4]] = torch.clamp(output[i, [2,4]], 0.0, im_dim[i,1])
            
            classes = load_classes('data/coco.names')
            colors = pkl.load(open("pallete", "rb"))
            #IPython.embed()
            list(map(lambda x: write(x, orig_im, frames), output))

            writeable = list(map(extract_markers, output))
            
            frame_info = {'frame_no': int(frames), 'detections': writeable}
            videoData['frame_data'].append(frame_info)
            clocky = False
            for j in output:
                if j[-1] == 74:
                    clocky = True
            
            if args.image and (frames - frameDetected) > args.skip and clocky:
                print("Writing frame %i to disk, number %i detected" % (frames, framesOut))
                cv2.imwrite('../input/stills/%05d.png' % framesOut, orig_im)
                frameDetected = frames
                framesOut += 1
            #cv2.imshow("frame", orig_im)
            #key = cv2.waitKey(1)
            #if key & 0xFF == ord('q'):
            #    break
            #out.write(orig_im)
            frames += 1
            #print("FPS of the video is {:5.2f}".format( frames / (time.time() - start)))
        else:
            break
    span.finish()
    import json
    requests.post(args.post_url, json=videoData)
    
    with open('out.json', 'w') as outfile:
        json.dump(videoData, outfile, indent=2)

