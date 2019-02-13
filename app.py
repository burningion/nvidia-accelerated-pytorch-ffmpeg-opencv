import time, os
import subprocess

from datadog import initialize, statsd
from ddtrace import tracer, patch
from ddtrace.contrib.flask import TraceMiddleware
from ddtrace.context import Context
from ddtrace.ext.priority import USER_KEEP

try:
    initialize(statsd_host=os.environ['DOGSTATSD_HOST_IP'], statsd_port=8125)
    tracer.configure(
    hostname=os.environ['DD_AGENT_SERVICE_HOST'],
    port=os.environ['DD_AGENT_SERVICE_PORT'],
)

except:
    print("No environment variables for Datadog set. App won't be instrumented.")

from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)

#patch traceware
traced_app = TraceMiddleware(app, tracer, service="video-inference-app", distributed_tracing=True)

#logging stuff
import logging
import json_log_formatter
import threading

# for correlating logs and traces

FORMAT = ('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
          '[dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] '
          '- %(message)s')
logging.basicConfig(format=FORMAT)

try:
    formatter = json_log_formatter.JSONFormatter()
    json_handler = logging.FileHandler(filename='/var/log/flask/mylog.json')
    json_handler.setFormatter(formatter)
    logger = logging.getLogger('my_json')
    logger.addHandler(json_handler)
    logger.setLevel(logging.INFO)
except:
    print("File logger not configured")

from collections import deque
inferenceQ = deque()

@app.route('/next-video-inference', methods=['GET'])
def next_inference():
    global inferenceQ
    try:
        os.chdir('/workspace/pytorch-yolo-v3/')
        shell_command = inferenceQ.popleft()
        span = tracer.current_span()
        logger.info('shell command for inference: %s' % shell_command)
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
        logger.info('next inference errored out because %s' % e)
        return jsonify({'que': 'empty'})

@app.route('/inference', methods=['POST'])
def inference():
    global inferenceQ
    params = request.get_json()
    shell_command = {'filename': params['filename'], 'postback_url': params['postback_url']}
    inferenceQ.append(shell_command)
    logger.info('Added %s to command queue, %i remaining' % (shell_command, len(inferenceQ)))
    return jsonify({'message': 'received'})

@app.route('/video-inference', methods=['POST'])
def video_inference():
    params = request.get_json()
    os.chdir('/workspace/pytorch-yolo-v3/')
    span = tracer.current_span()
    logger.info('Span ID and trace Id: %s %s' % (span.context.span_id, span.context.trace_id),
                extra={'job_category': 'inference', 'logger.name': 'gpu_logger'})

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
    return 'Hello world!'

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5007)
