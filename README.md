# Pytorch NVIDIA Docker Container with Hardware Accelerated ffmpeg / OpenCV 4

![Architecture of Deep Learning API](https://s3-us-west-2.amazonaws.com/makeartwithpython/the-clock-architecture-wm.png)

This is a work in progress Docker image for a talk demonstrating processing videos with GPUs.

It starts with the [NVIDIA Pytorch](https://ngc.nvidia.com/catalog/containers/nvidia%2Fpytorch) container, and then builds ffmpeg and OpenCV 4.0 from source with hardware acceleration. 

Running it via `nvidia-docker` gives us hardware access to the GPU, and lets us keep our host operating system clean / independent. 

This repo uses the latest release of Python 3 and Pytorch, adding hardware acceleration for the latest consumer NVIDIA GPU at this time (the 2080ti). Please note, in order for the GPU accelerated encoding and decoding to work, you'll also need to have at least the Linux Driver 

# Creating And Running the Image

For accerated encoding and decoding, your host machine must have the NVIDIA accelerated hardware encoder and decoder installed. The command to install is listed below, but may be different depending on the driver version you have installed.

As for building the image, right now there are just two things to be aware of. In our `make`, we're doing `-j4`, for the 4 CPUs I have on my dev machine. You may want to change this to something higher than that for running locally.

Besides that, this takes a __while__ to build. So uh, grab a cup of coffee or two...

```bash
$ sudo apt-get install libnvidia-decode-390 libnvidia-decode-390
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

## Splitting and Joining

There are now two new Python files that can be used to create `snippets` of videos featuring a specific feature in a video. For now, I've focused on clocks. You can copy the `splitter.py` and `joiner.py` files into your mounted volume that stores all videos.

Change into that directory on the container, and first run `splitter.py`. It will create a bunch of video snippets under the `slices/` directory. From there, you can run `joiner.py` to hit the `scraper` service, and grab all the unique videos for remixing.

The `joiner.py` file will create a `videolist.txt`. You can send that to ffmpeg's concat demuxer and generate a new video with the following ffmpeg command:

```bash
$ ffmpeg -f concat -i videolist.txt -c copy out.mp4
```

## Monitoring GPU Usage with NVIDIA DCGM exporter for Prometheus

You'll need to get your nodes with GPUs available within them, and then add a label to have the [NVIDIA DCGM exporter run as a DaemonSet](https://github.com/NVIDIA/gpu-monitoring-tools/tree/master/exporters/prometheus-dcgm) on those pods extracting GPU information.

In my case, running microk8s locally, where my attached machine has a GPU available in k8s:

```bash
$ microk8s.kubectl get nodes
NAME       STATUS   ROLES    AGE   VERSION
stankley   Ready    <none>   48d   v1.13.
$ microk8s.kubectl label nodes stankley hardware-type=NVIDIAGPU
$ microk8s.kubectl apply -f node-exporter-daemonset.yaml
```

When we've added the DaemonSet, we can check to see if it's running and exporting metrics by curling localhost:

```bash
$ curl -s localhost:9100/metrics | grep dcgm
# HELP dcgm_app_clock_violation Total throttling duration (in us).
# TYPE dcgm_app_clock_violation counter
dcgm_app_clock_violation{gpu="0",uuid="GPU-a612132df-7c52-b181-cf39-28065234123ac8"} -9.134403409224488e+18
....
....
```

With this, we can then extract these metrics with Datadog via annotations and auto-discovery.

