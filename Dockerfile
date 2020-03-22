#FROM nvcr.io/nvidia/pytorch:18.11-py3
FROM nvcr.io/nvidia/pytorch:19.02-py3
RUN apt-get update && apt-get -y install autoconf automake build-essential libass-dev libtool  pkg-config texinfo zlib1g-dev cmake mercurial libjpeg-dev libpng-dev libtiff-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev  libxvidcore-dev libx264-dev libx265-dev libnuma-dev libatlas-base-dev libopus-dev libvpx-dev gfortran unzip 
RUN git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git
RUN cd nv-codec-headers && make && make install
RUN git clone https://git.ffmpeg.org/ffmpeg.git
RUN cd ffmpeg &&  ./configure  --enable-shared --disable-static --enable-cuda --enable-cuvid --enable-libnpp --enable-libvpx --enable-libopus --enable-libx264  --enable-gpl --enable-pic --enable-libass --enable-nvenc --enable-nonfree --enable-libx265 --extra-cflags="-I/usr/local/cuda/include/ -fPIC" --extra-ldflags="-L/usr/local/cuda/lib64/ -Wl,-Bsymbolic"  && make -j4  && make install
RUN wget -O opencv.zip https://github.com/opencv/opencv/archive/4.0.0.zip && unzip opencv.zip && mv opencv-4.0.0 opencv
RUN wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.0.0.zip && unzip opencv_contrib.zip && mv opencv_contrib-4.0.0 opencv_contrib
RUN cd opencv && mkdir build && cd build && cmake -D CMAKE_BUILD_TYPE=RELEASE \
	-D CMAKE_INSTALL_PREFIX=/usr/local \
	-D INSTALL_PYTHON_EXAMPLES=ON \
	-D INSTALL_C_EXAMPLES=OFF \
	-D OPENCV_ENABLE_NONFREE=ON \
	-D OPENCV_EXTRA_MODULES_PATH=/workspace/opencv_contrib/modules \
  -D OPENCV_SKIP_PYTHON_LOADER=ON \
  -D PYTHON_LIBRARY=/opt/conda/lib/python3.6 \
  -D PYTHON_EXECUTABLE=/opt/conda/bin/python3 \
  -D PYTHON2_EXECUTABLE=/usr/bin/python2 \
  -D WITH_CUDA=ON \
  -D ENABLE_FAST_MATH=1 \
  -D CUDA_FAST_MATH=1 \
  -D WITH_CUBLAS=1 \
  -D WITH_FFMPEG=ON \
	-D BUILD_EXAMPLES=ON .. && make -j8 && make install
RUN cd /workspace/opencv/build/modules/python3 && make && make install
RUN ln -s /usr/local/python/python-3.6/cv2.cpython-36m-x86_64-linux-gnu.so /opt/conda/lib/python3.6/site-packages/cv2.so
RUN pip install pandas jupyter ipywidgets
RUN jupyter nbextension enable --py widgetsnbextension
RUN git clone https://github.com/ayooshkathuria/pytorch-yolo-v3 && cd pytorch-yolo-v3 && wget https://pjreddie.com/media/files/yolov3.weights
# Add Tini. Tini operates as a process subreaper for jupyter. This prevents
# kernel crashes.
ENV TINI_VERSION v0.6.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini
ENTRYPOINT ["/usr/bin/tini", "--"]
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
COPY app.py .
COPY video-to-json.py /workspace/pytorch-yolo-v3
COPY splitter.py .
COPY joiner.py .
COPY video-edges.py .
COPY test-video.mov .
EXPOSE 5007
ENV NVIDIA_VISIBLE_DEVICES all
CMD ["ddtrace-run", "python3", "app.py"]
# uncomment below and comment above to reenable jupyter notebook
#EXPOSE 8888
#CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]
