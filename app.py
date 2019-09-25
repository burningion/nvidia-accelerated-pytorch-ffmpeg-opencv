import os
import subprocess

from datadog import initialize, statsd
from ddtrace import tracer
from ddtrace.ext.priority import USER_KEEP

try:
    initialize(statsd_host=os.environ['DOGSTATSD_HOST_IP'], statsd_port=8125)
except:
    print("Couldn't initialize Dogstatsd")

from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)

from collections import deque
inferenceQ = deque()

@app.route('/next-video-inference', methods=['GET'])
def next_inference():
    global inferenceQ
    try:
        os.chdir('/workspace/pytorch-yolo-v3/')
        shell_command = inferenceQ.popleft()
        span = tracer.current_span()
        app.logger.info('shell command for inference: %s' % shell_command)
        subprocess.Popen(['python3',
                     '/workspace/pytorch-yolo-v3/video-to-json.py',
                     '--video',
                     shell_command['filename'],
                     '--post-url',
                     shell_command['postback_url'],
                     '--trace-id',
                     str(span.context.trace_id),
                     '--parent-id',
                     str(span.context.span_id),
                     '--sampling-priority',
                     str(USER_KEEP)])
        return jsonify({'inference': 'started'})
    except Exception as e:
        app.logger.info('next inference errored out because %s' % e)
        return jsonify({'que': 'empty'})

@app.route('/inference', methods=['POST'])
def inference():
    global inferenceQ
    params = request.get_json()
    shell_command = {'filename': params['filename'], 'postback_url': params['postback_url']}
    inferenceQ.append(shell_command)
    app.logger.info('Added %s to command queue, %i remaining' % (shell_command, len(inferenceQ)))
    return jsonify({'message': 'received'})

@app.route('/video-inference', methods=['POST'])
def video_inference():
    params = request.get_json()
    os.chdir('/workspace/pytorch-yolo-v3/')
    span = tracer.current_span()
    app.logger.info(f"Adding {params['filename']} to video inference queue")

    subprocess.Popen(['python3',
                     '/workspace/pytorch-yolo-v3/video-to-json.py',
                     '--video',
                     params['filename'],
                     '--post-url',
                     params['postback_url'],
                     '--trace-id',
                     str(span.context.trace_id),
                     '--parent-id',
                     str(span.context.span_id),
                     '--sampling-priority',
                     str(USER_KEEP)])

    return jsonify({'message': 'received'})

@app.route('/')
def hello_world():
    app.logger.info(f"Homepage of video inference API called")
    return 'Hello world!'

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5007)
