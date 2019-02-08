# Pytorch NVIDIA Docker Container with Hardware Accelerated ffmpeg / OpenCV 4

This is a work in progress Docker image for a talk demonstrating processing videos with GPUs.

It starts with the [NVIDIA Pytorch](https://ngc.nvidia.com/catalog/containers/nvidia%2Fpytorch) container, and then builds ffmpeg and OpenCV 4.0 from source with hardware acceleration. 

Running it via `nvidia-docker` gives us hardware access to the GPU, and lets us keep our host operating system clean / independent. 

This repo uses the latest release of Python 3 and Pytorch, adding hardware acceleration for the latest consumer NVIDIA GPU at this time (the 2080ti).

# Creating And Running the Image

Right now there are just two things to be aware of. In our `make`, we're doing `-j4`, for the 4 CPUs I have on my dev machine. You may want to change this to something higher than that for running locally.

Besides that, this takes a __while__ to build. So uh, grab a cup of coffee or two...

```bash
$ docker build -t ffmpegpytorch .
$ nvidia-docker run -it ffmpegpytorch /bin/bash
```

Once in the container, we can then run Python, and see our shell:

```bash
$ python3
Python 3.6.7 |Anaconda, Inc.| (default, Oct 23 2018, 19:16:44) 
[GCC 7.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import cv2
>>> inputVideo = cv2.VideoCapture('video.MOV')
>>> ok, frame = inputVideo.read()
>>> frame.shape
(1080, 1920, 3)
```

Remember, you can also mount directories and open up ports if you want to run Jupyter notebook, for example:

```bash
$ nvidia-docker run -p 8888:8888/tcp -it -v localdir:/workspace/localdir_in_container ffmpegpytorch /bin/bash
```

## Inference API

I've added the start of an inference API. The way you call it is:

```bash
$ curl --header "Content-Type: application/json"   --request POST   --data '{"filename": "/downloads/cuckoo.mp4", "postback_url": "http://10.152.183.141:5005/video-inference"}' http://10.152.183.139:5007/video-inference
```

The `postback_url` will get posted with the results of the inference in the video.
