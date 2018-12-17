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
$ docker run -it ffmpegpytorch /bin/bash
```
